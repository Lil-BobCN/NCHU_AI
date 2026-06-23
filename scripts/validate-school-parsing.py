import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def collect_samples(folder: Path, extensions: set[str], limit_per_ext: int, max_size_mb: int) -> list[Path]:
    grouped: dict[str, list[Path]] = defaultdict(list)
    max_bytes = max_size_mb * 1024 * 1024
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in extensions:
            continue
        if path.stat().st_size > max_bytes:
            continue
        grouped[ext].append(path)

    samples: list[Path] = []
    for ext in sorted(extensions):
        samples.extend(grouped[ext][:limit_per_ext])
    return samples


def _index_limits(meta: dict) -> list[dict]:
    sources = []
    for item in meta.get("sheets") or []:
        sources.append(item)
    for item in meta.get("tables") or []:
        sources.append(item)
    return [
        {
            "source": item.get("sheet_name") or item.get("table_index"),
            "index_mode": item.get("index_mode"),
            "row_count": item.get("row_count"),
            "indexed_row_count": item.get("indexed_row_count"),
            "full_index_limited": bool(item.get("full_index_limited")),
        }
        for item in sources
        if item.get("full_index_limited") or item.get("index_mode")
    ]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("folder", nargs="?", default=str(ROOT / "学校文件"))
    parser.add_argument(
        "--ext",
        nargs="*",
        default=[".doc", ".docx", ".xls", ".xlsx", ".pdf", ".jpg", ".png", ".zip", ".rar"],
    )
    parser.add_argument("--limit-per-ext", type=int, default=2)
    parser.add_argument("--max-size-mb", type=int, default=30)
    parser.add_argument("--disable-ocr", action="store_true")
    args = parser.parse_args()

    if args.disable_ocr:
        os.environ["OCR_ENABLED"] = "false"

    from app.services.chunk_service import ChunkService
    from app.services.parse_service import ParseService

    folder = Path(args.folder)
    extensions = {item if item.startswith(".") else f".{item}" for item in args.ext}
    samples = collect_samples(folder, extensions, args.limit_per_ext, args.max_size_mb)

    parser_service = ParseService()
    chunk_service = ChunkService()
    summary = Counter()
    results = []
    for index, path in enumerate(samples, start=1):
        print(f"[{index}/{len(samples)}] {path.name}", flush=True)
        try:
            parsed = parser_service.parse(path.name, path.read_bytes())
            chunks = chunk_service.split(parsed.text, parsed.meta)
            chunk_types = Counter(chunk.chunk_type for chunk in chunks)
            item = {
                "file": path.name,
                "ext": path.suffix.lower(),
                "parser": parsed.meta.get("parser"),
                "quality": parser_service.quality_score(parsed),
                "chars": len(parsed.text or ""),
                "chunks": len(chunks),
                "chunk_types": dict(chunk_types),
                "page_count": parsed.page_count,
                "needs_conversion": bool(parsed.meta.get("needs_conversion")),
                "needs_extraction": bool(parsed.meta.get("needs_extraction")),
                "ocr_required": bool(
                    parsed.meta.get("ocr_required") or parsed.meta.get("image_ocr_required")
                ),
                "index_limits": _index_limits(parsed.meta),
                "preview": " ".join((parsed.markdown or parsed.text or "").split())[:180],
            }
            summary[f"ok:{path.suffix.lower()}"] += 1
        except Exception as exc:
            item = {
                "file": path.name,
                "ext": path.suffix.lower(),
                "error": str(exc),
            }
            summary[f"fail:{path.suffix.lower()}"] += 1
        results.append(item)
        print(json.dumps(item, ensure_ascii=False), flush=True)

    print("\nSUMMARY")
    print(json.dumps(dict(summary), ensure_ascii=False, indent=2))
    print("\nRESULTS")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
