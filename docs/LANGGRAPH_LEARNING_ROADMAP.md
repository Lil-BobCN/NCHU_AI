# LangGraph 学习与项目落地路线

本文档面向技术新手，用来把 LangGraph 基础学习和本项目开发要求连起来。

## 1. 先理解项目现在是什么

当前项目是 `NCHU AI Counselor`，目标是做一个高校 AI 辅导员系统。

已有基础：

- 后端：FastAPI。
- 前端：React + TypeScript + Vite。
- 基础设施：PostgreSQL、Redis、MinIO、Milvus。
- 已有能力：登录、学生问答、资源列表、会话、知识维护、审计、统计、辅导员辅助。
- 当前限制：业务数据多为内存态 Demo；真实 RAG、真实学校资料、数据库持久化、文档解析链路仍需单独审批后实现。

项目已批准的技术方向：

- FastAPI 负责 API、鉴权、权限、审计和业务边界。
- LangGraph 负责后续 AI/RAG 工作流编排。
- LangChain 只作为局部工具库，用于模型、检索器、prompt、tool 等集成。

## 2. 用大白话理解 LangGraph

LangGraph 可以理解成“AI 工作流流程图”。

普通聊天接口通常像这样：

```text
用户问题 -> 调大模型 -> 返回回答
```

RAG 智能问答更像这样：

```text
用户问题
-> 改写问题
-> 判断意图
-> 读取会话记忆
-> 检索知识库
-> 重排序资料
-> 生成答案
-> 附上来源
-> 保存本轮上下文
-> 返回给前端
```

LangGraph 的价值，是把这些步骤拆成清晰的节点，并用状态在节点之间传递。

## 3. 三个最核心概念

### State

State 是整条流程共享的数据包。

比如本项目里，一个学生提问流程的 State 未来可能包含：

- `question`：学生原始问题。
- `rewritten_question`：改写后的检索问题。
- `intent`：问题意图，例如政策咨询、心理支持、办事流程。
- `conversation_id`：会话 ID。
- `retrieved_sources`：检索到的资料。
- `answer`：最终回答。
- `safety_flags`：安全风险标记。

### Node

Node 是流程中的一个步骤，本质上就是一个 Python 函数。

例如：

- `rewrite_query`：把口语化问题改写成适合检索的问题。
- `classify_intent`：判断问题类型。
- `retrieve_sources`：从知识库查资料。
- `generate_answer`：生成最终回答。

### Edge

Edge 是节点之间的连接线。

普通边表示“做完 A 之后做 B”。条件边表示“如果是心理风险问题走安全兜底，否则走普通 RAG 回答”。

## 4. 本项目的推荐学习顺序

### 第 0 课：看懂当前项目边界

目标：知道为什么不能一上来就直接做完整 RAG。

要看：

- `README.md`
- `PROJECT_STATE.md`
- `docs/development-process.md`
- `.omx/decisions/SDAR-0001-backend-ai-rag-orchestration.md`
- `.omx/decisions/SDAR-0008-real-model-student-chatbox.md`

你要记住的一句话：

> 真实模型聊天不等于 RAG；RAG、向量检索、真实学校资料都要单独审批。

### 第 1 课：写一个不接大模型的最小 LangGraph

目标：先理解 State、Node、Edge。

示例流程：

```text
输入问题 -> 判断是否校园相关 -> 生成固定回复
```

这一步不接 Qwen、不接 Milvus、不接数据库，方便学习和测试。

### 第 2 课：把项目现有内存知识库接成“假 RAG”

目标：把现有 `store.search_resources()` 包进 LangGraph 节点。

示例流程：

```text
输入问题 -> 检索内存知识 -> 组装回答和来源
```

这一步仍然不引入真实向量检索，所以风险较低。

### 第 3 课：把真实模型调用放进 Graph 的生成节点

目标：复用当前后端已经有的 Qwen/DashScope provider。

示例流程：

```text
输入问题 -> 加载会话上下文 -> 调 Qwen 生成流式回答 -> 保存内存会话
```

注意：仍然不声明“已接入真实学校知识库”。

### 第 4 课：设计正式 RAG Graph，但先只写规格

目标：根据学校技术方案画出正式工作流。

推荐流程：

```text
用户输入
-> 查询改写
-> 意图识别
-> 加载记忆
-> 三路召回
-> 重排序
-> 安全检查
-> 答案生成
-> 来源组装
-> 更新记忆
```

这一步涉及 RAG/vector/embedding/document ingestion，需要审批后再实现。

### 第 5 课：正式接 Milvus、Embedding、Rerank、来源引用

目标：进入学校项目要求里的完整 RAG 链路。

涉及内容：

- 文档切片。
- 向量化。
- Milvus 检索。
- 关键词/BM25 召回。
- 重排序。
- 来源引用。
- RAG 质量测试。

这一步是正式工程阶段，不能当学习 demo 随手加。

## 5. 第一阶段建议开发目标

为了边学边做，建议第一轮只做：

```text
LangGraph 学习版 student question graph
```

范围：

- 新增一个后端 workflow 模块。
- 使用 LangGraph 编排 3 个节点：安全分类、内存资源检索、回答组装。
- 暂时不接真实向量库。
- 暂时不改数据库 schema。
- 暂时不接真实学校资料。
- 用 pytest 验证普通问题、无资源问题、危机风险问题。

验收标准：

- 你能解释 State、Node、Edge 在代码里分别在哪里。
- 后端测试通过。
- API 行为不破坏现有学生问答接口。
- 回答不声称已经接入真实学校 RAG 知识库。

## 6. 学习时的代码入口

后端重点文件：

- `backend/app/api/v1/student.py`
- `backend/app/services/business.py`
- `backend/app/services/chat_model.py`
- `backend/app/schemas/business.py`
- `backend/tests/test_business_phase1.py`

未来建议新增文件：

- `backend/app/workflows/student_question_graph.py`
- `backend/tests/test_student_question_graph.py`

## 7. 我们的协作方式

每一步我会按这个节奏带你：

1. 先用大白话解释要学的概念。
2. 指给你看项目里对应的文件。
3. 写最小代码。
4. 跑测试。
5. 用结果反过来解释代码为什么这么写。
6. 再进入下一步。

