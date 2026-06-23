import re


DEFAULT_CONVERSATION_TITLE = "新的对话"
AUTO_CONVERSATION_TITLE_MAX_CHARS = 20
MANUAL_CONVERSATION_TITLE_MAX_CHARS = 50


def compact_title_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def truncate_title(value: str, max_chars: int, *, ellipsis: bool = True) -> str:
    text = compact_title_text(value)
    if len(text) <= max_chars:
        return text
    suffix = "..." if ellipsis and max_chars > 3 else ""
    return f"{text[: max_chars - len(suffix)].rstrip()}{suffix}"


def auto_title_from_question(question: str) -> str:
    title = truncate_title(question, AUTO_CONVERSATION_TITLE_MAX_CHARS)
    return title or DEFAULT_CONVERSATION_TITLE


def normalize_conversation_title(title: str | None) -> str:
    normalized = truncate_title(title or "", MANUAL_CONVERSATION_TITLE_MAX_CHARS)
    return normalized or DEFAULT_CONVERSATION_TITLE


def validate_manual_conversation_title(title: str | None) -> str:
    normalized = truncate_title(title or "", MANUAL_CONVERSATION_TITLE_MAX_CHARS)
    if not normalized:
        raise ValueError("标题不能为空")
    return normalized


def is_default_conversation_title(title: str | None) -> bool:
    return compact_title_text(title) in {"", DEFAULT_CONVERSATION_TITLE}


def should_auto_title_conversation(title: str | None, message_count: int | None) -> bool:
    return is_default_conversation_title(title) and int(message_count or 0) == 0
