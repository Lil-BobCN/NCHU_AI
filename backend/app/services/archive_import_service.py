from dataclasses import dataclass
from io import BytesIO
from pathlib import Path, PurePosixPath
import zipfile


class ArchiveExtractionError(RuntimeError):
    pass


@dataclass
class ArchiveEntry:
    name: str
    file_name: str
    data: bytes
    size: int


@dataclass
class ArchiveExtractResult:
    entries: list[ArchiveEntry]
    skipped: list[dict]


class ArchiveImportService:
    MAX_FILES = 50
    MAX_ENTRY_SIZE = 50 * 1024 * 1024
    MAX_TOTAL_SIZE = 100 * 1024 * 1024
    NESTED_ARCHIVE_EXTENSIONS = {".zip", ".rar"}

    def extract_supported_entries(self, file_name: str, data: bytes) -> ArchiveExtractResult:
        ext = Path(file_name).suffix.lower()
        if ext == ".zip":
            return self._extract_zip(data)
        if ext == ".rar":
            return self._extract_rar(data)
        raise ArchiveExtractionError(f"不支持的压缩包类型: {ext}")

    def _extract_zip(self, data: bytes) -> ArchiveExtractResult:
        entries: list[ArchiveEntry] = []
        skipped: list[dict] = []
        total_size = 0
        try:
            with zipfile.ZipFile(BytesIO(data)) as archive:
                for info in archive.infolist():
                    name = self._decode_zip_name(info)
                    if len(entries) >= self.MAX_FILES:
                        skipped.append({"name": name, "reason": "超过单次导入文件数量限制"})
                        continue
                    if info.is_dir():
                        continue
                    reason = self._skip_reason(name, info.file_size, total_size)
                    if reason:
                        skipped.append({"name": name, "reason": reason})
                        continue
                    file_data = archive.read(info)
                    total_size += len(file_data)
                    entries.append(
                        ArchiveEntry(
                            name=name,
                            file_name=self._safe_file_name(name),
                            data=file_data,
                            size=len(file_data),
                        )
                    )
        except zipfile.BadZipFile as exc:
            raise ArchiveExtractionError("ZIP 文件损坏或格式不正确") from exc
        return ArchiveExtractResult(entries=entries, skipped=skipped)

    def _extract_rar(self, data: bytes) -> ArchiveExtractResult:
        try:
            import rarfile
        except Exception as exc:
            raise ArchiveExtractionError("RAR 解压需要安装 rarfile，并配置 unrar/unar/bsdtar 解压工具") from exc

        entries: list[ArchiveEntry] = []
        skipped: list[dict] = []
        total_size = 0
        try:
            with rarfile.RarFile(BytesIO(data)) as archive:
                for info in archive.infolist():
                    name = info.filename
                    if len(entries) >= self.MAX_FILES:
                        skipped.append({"name": name, "reason": "超过单次导入文件数量限制"})
                        continue
                    if info.isdir():
                        continue
                    reason = self._skip_reason(name, info.file_size, total_size)
                    if reason:
                        skipped.append({"name": name, "reason": reason})
                        continue
                    file_data = archive.read(info)
                    total_size += len(file_data)
                    entries.append(
                        ArchiveEntry(
                            name=name,
                            file_name=self._safe_file_name(name),
                            data=file_data,
                            size=len(file_data),
                        )
                    )
        except Exception as exc:
            raise ArchiveExtractionError(f"RAR 解压失败: {exc}") from exc
        return ArchiveExtractResult(entries=entries, skipped=skipped)

    def _skip_reason(self, name: str, size: int, current_total_size: int) -> str | None:
        if self._unsafe_archive_name(name):
            return "压缩包路径不安全"
        ext = Path(name).suffix.lower()
        if ext in self.NESTED_ARCHIVE_EXTENSIONS:
            return "暂不自动导入嵌套压缩包"
        if not self._supported_inner_file(name):
            return "文件类型不支持导入"
        if size > self.MAX_ENTRY_SIZE:
            return "单文件超过大小限制"
        if current_total_size + size > self.MAX_TOTAL_SIZE:
            return "解压总大小超过限制"
        return None

    def _unsafe_archive_name(self, name: str) -> bool:
        normalized = name.replace("\\", "/")
        path = PurePosixPath(normalized)
        if path.is_absolute() or not path.name:
            return True
        if any(part in {"", ".", ".."} for part in path.parts):
            return True
        return ":" in path.parts[0]

    def _safe_file_name(self, name: str) -> str:
        return PurePosixPath(name.replace("\\", "/")).name

    def _decode_zip_name(self, info: zipfile.ZipInfo) -> str:
        name = info.filename
        if info.flag_bits & 0x800:
            return name
        try:
            raw = name.encode("cp437")
        except UnicodeEncodeError:
            return name
        for encoding in ("utf-8", "gbk", "gb2312", "big5"):
            try:
                decoded = raw.decode(encoding)
            except UnicodeDecodeError:
                continue
            if decoded == name:
                return decoded
            if self._contains_cjk(decoded) or self._looks_mojibake(name):
                return decoded
        return name

    def _contains_cjk(self, value: str) -> bool:
        return any("\u4e00" <= char <= "\u9fff" for char in value)

    def _looks_mojibake(self, value: str) -> bool:
        return any(char in value for char in ("�", "╬", "─", "╓", "╨", "▒", "▓", "│"))

    def _supported_inner_file(self, name: str) -> bool:
        return Path(name).suffix.lower() in {
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".xlsm",
            ".txt",
            ".md",
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".tif",
            ".tiff",
        }
