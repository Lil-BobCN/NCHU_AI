# Autoresearch Report: 工业级审批包格式

Date: 2026-05-17
Status: completed

## 研究问题

是否有比当前自定义审批包更成熟的工业级审批/决策记录格式，可用于本项目的技术选型、UI 结构、数据库结构、数据契约、开源组件引入等关键决策。

## 结论

有。推荐采用“Structured ADR / MADR 思路 + 产品经理审批字段”的混合格式。

不建议直接照搬单一模板：

- Nygard ADR 太轻，适合记录最终架构决策，但不够适合我们这种需要产品经理统一确认的问题清单。
- MADR 比 Nygard 更完整，包含备选方案和取舍，适合作为主体。
- Structured MADR 更适合我们，因为它强调结构化 metadata、完整 option analysis、risk assessment 和 audit sections。
- AWS/Microsoft 的 ADR 指南强调 key decisions、alternatives、status、confidence、consequences、append-only/supersede，这些应进入我们的审批规则。

因此，本项目建议使用：

**Structured Decision Approval Record，简称 SDAR。**

中文名：

**结构化决策审批记录。**

## 依据摘要

### Microsoft Azure Well-Architected ADR 指南

Microsoft 将 ADR 视为解决方案架构师的重要交付物，要求记录关键决策、被排除的备选方案、上下文、理由、影响和状态；并建议记录 confidence level，避免把 ADR 写成设计指南。

适合本项目吸收的点：

- 只记录架构重要或难以回滚的决策。
- 必须有 options considered。
- 必须有 decision outcome。
- 必须有 tradeoffs 和 confidence。
- 状态需要清晰：Proposed / Accepted / Superseded。
- 大型分阶段决策应拆成多个记录。

Source: https://learn.microsoft.com/en-ie/azure/well-architected/architect-role/architecture-decision-record

### AWS Prescriptive Guidance ADR

AWS 认为 ADR 可以支持团队对齐、记录战略方向、减少反复决策。它强调决策、上下文和考虑因素要被记录到 repository 中，避免“做了决定但无人知道为什么”。

适合本项目吸收的点：

- 决策要进入仓库，不能只停留在聊天记录。
- 决策要服务当前和未来参与者。
- 技术决策和流程决策都可以记录。

Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/welcome.html

### ADR Templates / MADR

ADR Templates 项目列出多种格式：MADR、Nygard ADR、Y-Statement 等。MADR 特别强调 considered options、pros/cons、tradeoff analysis、decision makers、confirmation。

适合本项目吸收的点：

- Nygard 结构：title/status/context/decision/consequences。
- MADR 结构：补充 options 和取舍。
- 可以使用 Markdown，直接存入仓库。

Source: https://adr.github.io/adr-templates/

### Structured MADR

Structured MADR 是 MADR 的结构化扩展，目标是 human-readable、machine-parseable、auditable、comprehensive，并增加 YAML frontmatter、option analysis、risk assessment 和 audit section。

适合本项目吸收的点：

- YAML frontmatter 适合后续机器检索和状态追踪。
- 必须包含风险和审计。
- 适合需要合规和长期维护的项目。

Source: https://smadr.dev/reference/specification/overview/

### Thoughtworks Lightweight ADR

Thoughtworks 将 Lightweight ADR 作为一种记录重要架构决策、上下文和后果的技术，并建议存入 source control，而不是只放在 wiki 或网站里。

适合本项目吸收的点：

- 决策文件应与代码同仓库保存。
- 适合演进式架构。
- 对外部审计和新成员理解有帮助。

Source: https://www.thoughtworks.com/en-au/radar/techniques/lightweight-architecture-decision-records

## 推荐格式：SDAR 结构化决策审批记录

### 文件命名

```text
.omx/decisions/SDAR-<number>-<slug>.md
```

示例：

```text
.omx/decisions/SDAR-0001-frontend-stack.md
.omx/decisions/SDAR-0002-backend-rag-orchestration.md
.omx/decisions/SDAR-0003-product-data-contract.md
```

### 状态枚举

- `draft`
- `pending-review`
- `approved`
- `rejected`
- `needs-changes`
- `superseded`

### 推荐模板

```md
---
id: SDAR-0000
title: <决策标题>
status: pending-review
date: YYYY-MM-DD
phase: <Phase / Node>
decision_owner: Product Manager
technical_owner: Codex
decision_type: <technical|ui|database|data-contract|component|security|deployment|product>
reversibility: <easy|moderate|hard>
confidence: <low|medium|high>
supersedes: []
superseded_by:
related_files: []
---

# SDAR-0000: <决策标题>

## 1. 一句话结论

<用一句话说明推荐选择。>

## 2. 需要你统一确认的问题

请产品经理统一回复：

1. 是否同意推荐方案？
2. 是否同意非目标和边界？
3. 是否同意进入下一任务节点？
4. 是否有必须修改的地方？

## 3. 背景与上下文

- 当前阶段：
- 当前约束：
- 已批准的上游决策：
- 当前问题为什么现在必须决策：

## 4. 决策驱动因素

- 业务目标：
- 技术目标：
- 合规/隐私目标：
- 成本/部署目标：
- 可维护性目标：

## 5. 推荐方案

<说明推荐方案。>

## 6. 备选方案对比

| 方案 | 优点 | 缺点 | 成本 | 风险 | 是否推荐 |
| --- | --- | --- | --- | --- | --- |
| A | | | | | |
| B | | | | | |
| C | | | | | |

## 7. 为什么推荐

<说明关键取舍。>

## 8. 影响范围

- 前端：
- 后端：
- 数据库：
- API：
- 测试：
- 部署：
- 文档：

## 9. 数据边界与合规影响

- 是否涉及真实学生数据：
- 是否涉及学校资源：
- 是否涉及第三方服务：
- 是否存在数据出域：
- 脱敏/审计要求：

## 10. 风险、缓解与回滚

| 风险 | 严重性 | 缓解方式 | 回滚方式 |
| --- | --- | --- | --- |
| | | | |

## 11. 验收方式

- 验收证据：
- 测试方式：
- 不通过时如何处理：

## 12. 非目标

- 本次不做：
- 后续阶段再做：

## 13. 审批结果

- 状态：pending-review
- 审批日期：
- 审批证据：
- 修改要求：

## 14. 后续任务

- 下一任务节点：
- 需要新增的计划/测试/代码文件：
- 停止规则：
```

## 对本项目的建议

从下一次审批开始，使用 SDAR，而不是普通“审批包”。

适用范围：

- Phase 1 前端技术栈。
- Phase 1 信息架构/路由图。
- 设计系统与组件库。
- Contract/Data Boundary Node。
- 数据库 schema。
- LangGraph/LangChain/LangSmith/RAG 细化方案。
- Milvus collection/vector schema。
- 模型 provider、embedding、rerank。
- Docker/阿里云部署拓扑。

不需要使用 SDAR 的事项：

- 小文案修改。
- 已审批范围内的普通代码实现。
- 测试修复。
- 日志补充。

## 推荐下一步

1. 新建 `.omx/decisions/` 目录。
2. 将已批准的后端 AI/RAG 编排审批包转换为 `SDAR-0001-backend-ai-rag-orchestration.md`。
3. 后续 Phase 1 前端技术栈使用 `SDAR-0002-frontend-stack.md`。

