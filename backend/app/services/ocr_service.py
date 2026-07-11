"""OCR 服务：懒加载 PaddleOCR 并把图片或扫描页转换为文本。"""

from dataclasses import dataclass
import os
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from typing import Any


@dataclass
class OcrLine:
    text: str
    confidence: float
    box: Any | None = None


@dataclass
class OcrResult:
    text: str
    lines: list[OcrLine]
    engine: str = "paddleocr"
    error: str | None = None


class PaddleOcrService:
    def __init__(self, lang: str = "ch", use_gpu: bool = False, min_confidence: float = 0.45) -> None:
        self.lang = lang
        self.use_gpu = use_gpu
        self.min_confidence = min_confidence
        self._engine: Any | None = None
        self._load_error: str | None = None

    def ocr_image_bytes(self, image_bytes: bytes, suffix: str = ".png") -> OcrResult:
        if not image_bytes:
            return OcrResult(text="", lines=[], error="empty image")
        try:
            engine = self._get_engine()
        except Exception as exc:
            return OcrResult(text="", lines=[], error=str(exc))

        temp_path = ""
        try:
            with NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp.write(image_bytes)
                temp_path = temp.name
            raw = self._run_engine(engine, temp_path)
            lines = [
                line
                for line in self._collect_lines(raw)
                if line.text.strip() and line.confidence >= self.min_confidence
            ]
            return OcrResult(text="\n".join(line.text for line in lines), lines=lines)
        except Exception as exc:
            return OcrResult(text="", lines=[], error=str(exc))
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

    def _get_engine(self):
        if self._engine is not None:
            return self._engine
        if self._load_error:
            raise RuntimeError(self._load_error)
        self._prepare_cache_dirs()
        try:
            from paddleocr import PaddleOCR
        except Exception as exc:
            self._load_error = f"PaddleOCR is not installed or failed to import: {exc}"
            raise RuntimeError(self._load_error) from exc

        attempts = [
            {
                "lang": self.lang,
                "ocr_version": "PP-OCRv4",
                "use_textline_orientation": False,
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "enable_mkldnn": False,
                "device": "cpu",
            },
            {
                "lang": self.lang,
                "use_textline_orientation": False,
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "text_detection_model_name": "PP-OCRv5_mobile_det",
                "text_recognition_model_name": "PP-OCRv5_mobile_rec",
                "enable_mkldnn": False,
                "device": "cpu",
            },
            {
                "use_angle_cls": True,
                "lang": self.lang,
                "show_log": False,
                "use_gpu": self.use_gpu,
            },
            {"lang": self.lang, "show_log": False, "enable_mkldnn": False},
            {"lang": self.lang, "enable_mkldnn": False},
        ]
        last_error: Exception | None = None
        for kwargs in attempts:
            try:
                self._engine = PaddleOCR(**kwargs)
                return self._engine
            except Exception as exc:
                last_error = exc
                continue
        if last_error:
            raise RuntimeError(f"Failed to initialize PaddleOCR: {last_error}") from last_error
        raise RuntimeError("Failed to initialize PaddleOCR")

    def _prepare_cache_dirs(self) -> None:
        root = Path(__file__).resolve().parents[3]
        cache_root = self._default_cache_root(root)
        self._prepare_process_home(cache_root)
        xdg_cache = self._writable_cache_path("XDG_CACHE_HOME", cache_root)
        paddlex_cache = self._writable_cache_path("PADDLE_PDX_CACHE_HOME", cache_root / "paddlex")
        paddle_cache = self._writable_cache_path("PADDLE_HOME", cache_root / "paddle")
        hf_cache = self._writable_cache_path("HF_HOME", cache_root / "huggingface")
        modelscope_cache = self._writable_cache_path("MODELSCOPE_CACHE", cache_root / "modelscope")
        for path in (cache_root, xdg_cache, paddlex_cache, paddle_cache, hf_cache, modelscope_cache):
            path.mkdir(parents=True, exist_ok=True)
        os.environ["XDG_CACHE_HOME"] = str(xdg_cache)
        os.environ["PADDLE_PDX_CACHE_HOME"] = str(paddlex_cache)
        os.environ["PADDLE_HOME"] = str(paddle_cache)
        os.environ["HF_HOME"] = str(hf_cache)
        os.environ["MODELSCOPE_CACHE"] = str(modelscope_cache)
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

    def _prepare_process_home(self, cache_root: Path) -> None:
        home_cache = Path.home() / ".cache"
        if self._can_write(home_cache):
            return
        cache_root.mkdir(parents=True, exist_ok=True)
        os.environ["HOME"] = str(cache_root)
        os.environ["USERPROFILE"] = str(cache_root)
        drive = cache_root.drive
        if drive:
            os.environ["HOMEDRIVE"] = drive
            os.environ["HOMEPATH"] = str(cache_root)[len(drive) :]

    def _default_cache_root(self, project_root: Path) -> Path:
        project_cache = project_root / ".cache"
        if str(project_cache).isascii():
            return project_cache
        return Path(gettempdir()) / "agent_rag_ocr_cache"

    def _writable_cache_path(self, env_name: str, fallback: Path) -> Path:
        configured = os.environ.get(env_name)
        if configured:
            path = Path(configured)
            if self._can_write(path):
                return path
        return fallback

    def _can_write(self, path: Path) -> bool:
        probe = path / ".write-test"
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def _run_engine(self, engine, image_path: str):
        if hasattr(engine, "ocr"):
            try:
                return engine.ocr(image_path, cls=True)
            except TypeError:
                return engine.ocr(image_path)
        if hasattr(engine, "predict"):
            return engine.predict(image_path)
        raise RuntimeError("Unsupported PaddleOCR engine API")

    def _collect_lines(self, node: Any) -> list[OcrLine]:
        node = self._normalize_node(node)
        lines: list[OcrLine] = []
        if node is None:
            return lines
        if isinstance(node, dict):
            lines.extend(self._collect_dict_lines(node))
            for value in node.values():
                lines.extend(self._collect_lines(value))
            return lines
        if isinstance(node, (list, tuple)):
            old_line = self._old_api_line(node)
            if old_line:
                return [old_line]
            for item in node:
                lines.extend(self._collect_lines(item))
            return lines
        return lines

    def _collect_dict_lines(self, data: dict) -> list[OcrLine]:
        texts = data.get("rec_texts") or data.get("texts")
        if isinstance(texts, list):
            scores = data.get("rec_scores") or data.get("scores") or []
            boxes = data.get("rec_boxes") or data.get("dt_polys") or data.get("boxes") or []
            lines: list[OcrLine] = []
            for index, text in enumerate(texts):
                if not isinstance(text, str):
                    continue
                score = self._safe_float(scores[index] if index < len(scores) else 1.0)
                box = boxes[index] if index < len(boxes) else None
                lines.append(OcrLine(text=text, confidence=score, box=self._json_safe(box)))
            return lines
        text = data.get("text")
        if isinstance(text, str):
            score = self._safe_float(data.get("score") or data.get("confidence") or 1.0)
            return [OcrLine(text=text, confidence=score, box=self._json_safe(data.get("box")))]
        return []

    def _old_api_line(self, node: list | tuple) -> OcrLine | None:
        if len(node) < 2 or not isinstance(node[1], (list, tuple)):
            return None
        payload = node[1]
        if len(payload) < 2 or not isinstance(payload[0], str):
            return None
        return OcrLine(
            text=payload[0],
            confidence=self._safe_float(payload[1]),
            box=self._json_safe(node[0]),
        )

    def _normalize_node(self, node: Any) -> Any:
        for attr in ("json", "to_json"):
            value = getattr(node, attr, None)
            if value is None:
                continue
            try:
                return value() if callable(value) else value
            except TypeError:
                continue
        return node

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except Exception:
            return 1.0

    def _json_safe(self, value: Any) -> Any:
        if hasattr(value, "tolist"):
            return value.tolist()
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._json_safe(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
