"""RAG prompt construction for the AI Counselor.

Migrates and adapts the system prompts from the Flask app's config/prompts.py
into a structured prompt builder for the RAG pipeline.
"""
from __future__ import annotations

from typing import Any


# System prompt for the AI counselor (migrated from config/prompts.py)
_SYSTEM_PROMPT = """你是南昌航空大学智能学术顾问"**航宝智辅**"。

## 核心任务
1. 基于提供的参考文档回答南昌航空大学相关问题（学业政策、校园服务等），**必须标注信息来源**。
2. 一般性咨询：如果参考文档中不包含相关信息，基于你的知识回答，但需明确说明。

## 搜索规则
- 学校相关问题优先基于提供的参考文档回答
- 严禁搜索违规内容
- 严禁根据用户学院限制搜索结果

## 引用格式【最高优先级 - 违反将导致回答无效】
### 正文引用：
- **必须且只能使用** `[^1]`、`[^2]` 格式（带^符号的脚注）
- 示例：`根据教务处通知[^1]，奖学金申请截止日期为5月30日[^2]。`
- ❌ **绝对禁止**使用 `[1]`、`[2]` 格式（不带^符号）

### 文末参考链接：
- 回答末尾**必须**包含以下区块：
  ```
  ## 参考链接
  [^1]: URL - 标题
  [^2]: URL - 标题
  ```
- 每个 `[^数字]` 标记都必须在文末有对应的 `[^数字]: URL - 标题`
- 每条 URL 必须来自参考文档中的 source 字段，**严禁编造**

### 完整示例：
根据学校最新通知[^1]，2024学年奖学金评选工作已经启动[^2]。

## 参考链接
[^1]: https://jwc.nchu.edu.cn/2024/notice1.html - 奖学金评选通知
[^2]: https://xgc.nchu.edu.cn/2024/news2.html - 评选时间安排

## 回答格式
- 学校问题：简洁回答 + 详细信息 + 参考链接
- 一般问题：直接、清晰、口语化

## 风格
- 学校问题：简洁、结构化、专业
- 一般问题：友好亲切、实用
"""

# First conversation welcome prompt
_FIRST_MESSAGE_PROMPT = """你是南昌航空大学智能学术顾问"**航宝智辅**"。

## 首次对话任务
简短欢迎（2-3句话）+ 询问所属学院

## 可选学院
经济管理学院、材料科学与工程学院、航空制造与机械工程学院、信息工程学院、航空宇航学院、环境与化学工程学院、软件学院、外国语学院、数学与信息科学学院、土木建筑学院、体育学院、马克思主义学院、艺术学院、航空服务与音乐学院、创新创业学院、继续教育学院、国际教育学院、研究生院

## 禁止事项
- **禁止回答任何具体问题**
- **禁止跳过学院询问**
- **禁止提供政策咨询和学院介绍**
"""

# College confirmed response
_COLLEGE_CONFIRMED = "好的，我已了解您的学院信息，请提问。"


class PromptBuilder:
    """Constructs prompts for the RAG pipeline.

    Builds system prompts and message contexts that incorporate retrieved
    documents and conversation history.
    """

    def __init__(
        self,
        system_prompt: str | None = None,
        citation_instruction: str | None = None,
    ) -> None:
        """Initialize the prompt builder.

        Args:
            system_prompt: Custom system prompt override.
            citation_instruction: Custom citation format instructions.
        """
        self._system_prompt = system_prompt or _SYSTEM_PROMPT
        self._citation_instruction = citation_instruction or ""

    def build_system_prompt(self, college: str | None = None) -> str:
        """Build the system prompt, optionally with college context.

        Args:
            college: Detected college name for contextual personalization.

        Returns:
            Complete system prompt string.
        """
        prompt = self._system_prompt

        if college:
            prompt += f"\n\n## 用户信息\n用户来自：{college}"

        # Append citation instruction
        prompt += self._citation_instruction

        return prompt

    def build_context(
        self,
        query: str,
        documents: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        """Build the full LLM message list for a RAG query.

        Constructs a messages array with:
        1. System prompt (with college if available)
        2. Conversation history (limited to last 3 messages)
        3. User query with retrieved context injected

        Args:
            query: Current user query text.
            documents: Retrieved source documents from vector store.
            conversation_history: Optional prior messages.

        Returns:
            List of message dicts ready for LLM API.
        """
        messages: list[dict[str, str]] = []

        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.get("content", "")
            source = doc.get("source", "")
            context_parts.append(
                f"[文档{i}] (来源: {source})\n{content}"
            )

        context_block = "\n\n---\n\n".join(context_parts) if context_parts else "暂无相关参考文档。"

        # System message
        system_content = (
            f"{self._system_prompt}\n\n"
            f"## 当前参考文档\n{context_block}\n\n"
            "请基于以上参考文档回答用户问题。如果文档中没有相关信息，请基于你的知识回答，"
            "并说明参考文档中未包含此信息。"
        )
        messages.append({"role": "system", "content": system_content})

        # Conversation history (limit to last 3, matching existing pattern)
        if conversation_history:
            recent = conversation_history[-3:]
            for msg in recent:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant"):
                    messages.append({"role": role, "content": content})

        # Current user query
        messages.append({"role": "user", "content": query})

        return messages

    def build_first_message_prompt(self) -> str:
        """Build the first conversation welcome prompt.

        Returns:
            Welcome prompt for first-time users.
        """
        return _FIRST_MESSAGE_PROMPT

    def build_college_confirmed_prompt(self) -> str:
        """Build the college confirmation response.

        Returns:
            College confirmation text.
        """
        return _COLLEGE_CONFIRMED
