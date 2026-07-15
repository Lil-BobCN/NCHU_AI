"""
切片服务。把解析后的文档文本拆成适合检索和向量化的 chunk，并保留页码、章节等元数据。
"""

import json
import re
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.services.hash_service import sha256_text
from app.services.rag_settings_service import RagSettingsService


@dataclass
class Chunk:
    chunk_no: int
    content: str
    content_hash: str
    page_start: int | None
    page_end: int | None
    section_path: str | None
    chunk_type: str = "text"
    metadata: dict = field(default_factory=dict)


class ChunkService:
    RAG_BLOCK_RE = re.compile(
        r"<!--\s*RAG_BLOCK\s+(?P<meta>\{.*?\})\s*-->\s*"
        r"(?P<content>.*?)\s*<!--\s*RAG_BLOCK_END\s*-->",
        re.DOTALL,
    )

    def __init__(self) -> None:
        self.settings = get_settings()
        self.rag_settings = RagSettingsService().get_effective()

    def split(self, text: str, parse_meta: dict | None = None) -> list[Chunk]:
        if parse_meta and parse_meta.get("skip_chunking"):
            return []

        page_blocks = self._split_pages(text)
        chunks: list[Chunk] = []
        for page_no, page_text in page_blocks:
            for block_type, block_meta, block_content in self._split_structured_blocks(page_text):
                clean_content = self._clean_page_text(block_content)
                if block_type == "table":
                    chunks.extend(self._split_table_block(clean_content, block_meta, page_no, len(chunks)))
                    continue

                chunk_type = "ocr" if block_type in {"ocr_page", "image_ocr"} else "text"
                metadata = {**block_meta}
                for part in self._split_text(clean_content):
                    clean = part.strip()
                    if not clean:
                        continue
                    chunks.append(
                        self._make_chunk(
                            chunk_no=len(chunks) + 1,
                            content=clean,
                            page_no=page_no or self._metadata_page(metadata),
                            chunk_type=chunk_type,
                            metadata=metadata,
                            section_path=self._section_path(clean, metadata),
                        )
                    )
        return self._apply_document_budget(chunks)

    def _split_structured_blocks(self, text: str) -> list[tuple[str, dict, str]]:
        blocks: list[tuple[str, dict, str]] = []
        cursor = 0
        for match in self.RAG_BLOCK_RE.finditer(text):
            prefix = text[cursor : match.start()].strip()
            if prefix:
                blocks.append(("text", {}, prefix))
            metadata = self._loads_metadata(match.group("meta"))
            block_type = str(metadata.get("type") or "text")
            blocks.append((block_type, metadata, match.group("content")))
            cursor = match.end()
        suffix = text[cursor:].strip()
        if suffix:
            blocks.append(("text", {}, suffix))
        return blocks or [("text", {}, text)]

    def _split_table_block(
        self,
        content: str,
        metadata: dict,
        page_no: int | None,
        existing_count: int,
    ) -> list[Chunk]:
        lines = [line.rstrip() for line in content.splitlines() if line.strip()]
        table_start = next((idx for idx, line in enumerate(lines) if line.lstrip().startswith("|")), None)
        if table_start is None:
            return [
                self._make_chunk(
                    chunk_no=existing_count + 1,
                    content=content.strip(),
                    page_no=page_no or self._metadata_page(metadata),
                    chunk_type="table",
                    metadata=metadata,
                    section_path=self._section_path(content, metadata),
                )
            ]

        title_lines = lines[:table_start]
        header_line = lines[table_start]
        separator_line = lines[table_start + 1] if table_start + 1 < len(lines) else ""
        if not self._is_markdown_separator(separator_line):
            separator_line = "| --- |"
            row_lines = lines[table_start + 1 :]
        else:
            row_lines = lines[table_start + 2 :]

        base_lines = [*title_lines, header_line, separator_line]
        if not row_lines:
            body = "\n".join(base_lines)
            return [
                self._make_chunk(
                    chunk_no=existing_count + 1,
                    content=body,
                    page_no=page_no or self._metadata_page(metadata),
                    chunk_type="table",
                    metadata={
                        **metadata,
                        "row_start": metadata.get("row_start"),
                        "row_end": metadata.get("row_end"),
                    },
                    section_path=self._section_path(body, metadata),
                )
            ]

        chunks: list[Chunk] = []
        base_text = "\n".join(base_lines)
        row_limit = max(1, int(self.rag_settings.get("table_chunk_rows", 50)))

        for start in range(0, len(row_lines), row_limit):
            rows = row_lines[start : start + row_limit]
            chunks.append(
                self._table_chunk(
                    existing_count + len(chunks) + 1,
                    base_text,
                    rows,
                    start,
                    page_no,
                    metadata,
                )
            )
        return chunks

    def _apply_document_budget(self, chunks: list[Chunk]) -> list[Chunk]:
        max_chunks = int(self.rag_settings.get("max_document_chunks", 0) or 0)
        max_chars = int(self.rag_settings.get("max_embedding_chars_per_document", 0) or 0)
        if max_chunks <= 0 and max_chars <= 0:
            return chunks

        kept: list[Chunk] = []
        char_total = 0
        truncated = False
        for chunk in chunks:
            next_count = len(kept) + 1
            next_chars = char_total + len(chunk.content)
            if (max_chunks > 0 and next_count > max_chunks) or (max_chars > 0 and kept and next_chars > max_chars):
                truncated = True
                break
            kept.append(chunk)
            char_total = next_chars

        if truncated and kept:
            kept[-1].metadata = {
                **kept[-1].metadata,
                "document_budget_truncated": True,
                "original_chunk_count": len(chunks),
                "indexed_chunk_count": len(kept),
                "indexed_char_count": char_total,
            }
        return kept

    def _table_chunk(
        self,
        chunk_no: int,
        base_text: str,
        row_lines: list[str],
        row_offset: int,
        page_no: int | None,
        metadata: dict,
    ) -> Chunk:
        content = base_text + "\n" + "\n".join(row_lines)
        first_data_row = self._first_data_row(metadata)
        row_start = first_data_row + row_offset if first_data_row is not None else metadata.get("row_start")
        row_end = row_start + len(row_lines) - 1 if isinstance(row_start, int) else metadata.get("row_end")
        chunk_meta = {
            **metadata,
            "row_start": row_start,
            "row_end": row_end,
            "row_count": len(row_lines),
        }
        return self._make_chunk(
            chunk_no=chunk_no,
            content=content.strip(),
            page_no=page_no or self._metadata_page(metadata),
            chunk_type="table",
            metadata=chunk_meta,
            section_path=self._section_path(content, chunk_meta),
        )

    def _first_data_row(self, metadata: dict) -> int | None:
        header_row = metadata.get("header_row")
        if isinstance(header_row, int):
            return header_row + 1
        row_start = metadata.get("row_start")
        if isinstance(row_start, int):
            return row_start + 1
        return None

    def _make_chunk(
        self,
        chunk_no: int,
        content: str,
        page_no: int | None,
        chunk_type: str,
        metadata: dict,
        section_path: str | None,
    ) -> Chunk:
        return Chunk(
            chunk_no=chunk_no,
            content=content,
            content_hash=sha256_text(content),
            page_start=page_no,
            page_end=page_no,
            section_path=section_path,
            chunk_type=chunk_type,
            metadata=metadata,
        )

    def _clean_page_text(self, text: str) -> str:
        text = re.sub(
            r"(?:(?:庄艳蓓\s*)?\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*){3,}",
            " ",
            text,
        )
        text = re.sub(
            r"(?:(?:庄艳蓓\s*)?\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?\s*){3,}",
            " ",
            text,
        )
        return re.sub(r"[ \t]{2,}", " ", text)

    def _split_pages(self, text: str) -> list[tuple[int | None, str]]:
        matches = list(re.finditer(r"\[第(\d+)页\]", text))
        if not matches:
            return [(None, text)]
        blocks: list[tuple[int | None, str]] = []
        for idx, match in enumerate(matches):
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            blocks.append((int(match.group(1)), text[start:end]))
        return blocks

    def _split_text(self, text: str) -> list[str]:
        size = int(self.rag_settings["chunk_size"])
        overlap = int(self.rag_settings["chunk_overlap"])
        paragraphs = [item.strip() for item in re.split(r"\n\s*\n|\r\n\s*\r\n", text) if item.strip()]
        parts: list[str] = []
        buffer = ""
        for paragraph in paragraphs:
            if len(buffer) + len(paragraph) <= size:
                buffer = f"{buffer}\n\n{paragraph}".strip()
                continue
            if buffer:
                parts.append(buffer)
            if len(paragraph) <= size:
                buffer = paragraph
            else:
                parts.extend(self._window(paragraph, size, overlap))
                buffer = ""
        if buffer:
            parts.append(buffer)
        return self._apply_text_overlap(parts, overlap)

    def _apply_text_overlap(self, parts: list[str], overlap: int) -> list[str]:
        if overlap <= 0 or len(parts) <= 1:
            return parts
        overlapped = [parts[0]]
        for previous, current in zip(parts, parts[1:], strict=False):
            prefix = self._overlap_tail(previous, overlap)
            if prefix and not current.startswith(prefix):
                overlapped.append(f"{prefix}\n\n{current}".strip())
            else:
                overlapped.append(current)
        return overlapped

    def _overlap_tail(self, text: str, overlap: int) -> str:
        clean = text.strip()
        if not clean:
            return ""
        if len(clean) <= overlap:
            return clean
        tail = clean[-overlap:]
        breakpoints = ["\n\n", "\n", "。", "；", ";"]
        for marker in breakpoints:
            index = tail.find(marker)
            if 0 <= index < len(tail) - 1:
                return tail[index + len(marker) :].strip()
        return tail.strip()

    def _window(self, text: str, size: int, overlap: int) -> list[str]:
        # 电话号码正则：匹配固话（如 0791-83863005）和手机号，避免切分截断
        phone_re = re.compile(r"0\d{2,3}[-—]?\d{7,8}|1[3-9]\d{9}")
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            # 边界保护：如果切分点落在电话号码内，向后调整到号码结束位置
            if end < len(text):
                search_start = max(0, end - 30)
                search_end = min(len(text), end + 30)
                for m in phone_re.finditer(text[search_start:search_end]):
                    match_start = search_start + m.start()
                    match_end = search_start + m.end()
                    if match_start < end < match_end:
                        end = match_end
                        break
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start = max(0, end - overlap)
        return chunks

    def _section_path(self, text: str, metadata: dict) -> str | None:
        if metadata.get("sheet_name"):
            row_start = metadata.get("row_start")
            row_end = metadata.get("row_end")
            suffix = f" 行{row_start}-{row_end}" if row_start and row_end else ""
            return f"工作表：{metadata['sheet_name']}{suffix}"
        if metadata.get("table_index"):
            return f"表格 {metadata['table_index']}"
        if metadata.get("image_index"):
            return f"图片 {metadata['image_index']} OCR"
        if metadata.get("page"):
            return f"第 {metadata['page']} 页 OCR"
        return self._guess_section(text)

    def _guess_section(self, text: str) -> str | None:
        head = text[:500].replace("\n", " ").strip()
        patterns = [
            r"^#{1,6}\s+(.{2,80})",
            r"([一二三四五六七八九十]+、[^。；;]{2,40})",
            r"(第[一二三四五六七八九十百\d]+[章节条][^。；;]{0,40})",
            r"(\d+[.、][^。；;]{2,40})",
        ]
        for pattern in patterns:
            match = re.search(pattern, head)
            if match:
                return re.sub(r"\s+", " ", match.group(1)).strip()[:120]
        return None

    def _loads_metadata(self, raw: str) -> dict:
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _metadata_page(self, metadata: dict) -> int | None:
        page = metadata.get("page")
        return page if isinstance(page, int) else None

    def _is_markdown_separator(self, line: str) -> bool:
        clean = line.strip()
        return clean.startswith("|") and bool(re.fullmatch(r"[\s|:\-]+", clean))
