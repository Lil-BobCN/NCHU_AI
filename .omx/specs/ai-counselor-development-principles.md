# AI 辅导员系统开发方式总纲

日期: 2026-05-16  
状态: 后续 AI / OMX skills 接手时优先阅读的单页总纲

## 1. 核心开发思想

本项目不走“从零手写所有后端通用能力”的路线。

正式开发方式是：

**FastAPI 作为核心业务后端，外接成熟开源组件，把常见后端功能快速拼起来，项目主要精力用于 AI 辅导员业务逻辑。**

也就是说：
- FastAPI 负责业务 API、RAG 编排、权限判断、数据模型、学校 SSO 适配。
- PostgreSQL 负责结构化业务数据。
- Redis 负责缓存、会话、任务状态和轻量异步队列基础。
- MinIO 负责原始文档和对象存储。
- Milvus 负责正式向量数据库。
- Docker Compose 负责本地、阿里云 Linux、校内 Linux 私有化部署的可复现基础。
- 宝塔面板可作为服务器运维、反向代理、证书和日志管理工具，但不替代仓库内的 Compose、环境变量和 smoke 验证。

## 2. 产品定位

当前已确认的产品定位是：

**校本知识库驱动的学生事务自助问答系统 + 辅导员工作辅助平台。**

服务对象优先级：
1. 学生：高频事务问答、政策流程查询、校内资源入口。
2. 辅导员：通知文案、谈话提纲、台账初稿、高频问题分析。
3. 学工/学院管理员：知识库维护、权限管理、日志审计、基础统计。

第一版不做完整智慧学工系统，不把自动决策、风险闭环、大屏、数字人作为主线。

## 3. P0/P1 范围

P0 优先建立：
- FastAPI 正式业务后端。
- NCHU SSO Adapter + 本地开发登录。
- 用户、角色、组织、学院、班级基础模型。
- 知识库、文档、问答、会话、日志领域模型骨架。
- PostgreSQL、Redis、MinIO、Milvus 的业务使用边界。
- 基础权限、审计、健康检查、smoke 验证。

P1 优先建立：
- 学生端问答 API。
- 校内官方资源和办理链接直达。
- RAG 检索、重排、来源引用。
- 多轮会话和历史记录。
- 知识库上传、解析、入库、重建索引、纠错。
- 管理后台的知识库维护和日志检索。
- 辅导员减负能力：通知文案、谈话提纲、工作总结/台账初稿、高频问题分析。
- 基础统计：咨询量、问题分类、高频问题、无答案问题、知识库命中率。

## 4. 明确后置能力

以下能力不进入第一版主线，除非后续明确重新规划：
- 心理诊断。
- 自动奖惩、处分、资助资格最终决策。
- 全域学生画像。
- 风险闭环预警。
- 一网通办自动代办。
- 数字人和视频化交互。
- 大屏决策中心。
- 企业微信、公众号、多终端全量发布。

AI 只能辅助，不替代人工辅导员和学校正式流程。

## 5. 学校 SSO 路线

南昌航空大学统一身份认证公开信息显示，学校登录更接近自研 SSO 回调，不是标准 OIDC/CAS 直接接入形态。

正式建议：
- P0 使用 FastAPI 内部的 `NchuSsoAdapter` 适配学校 SSO。
- 本地开发保留 mock / local login，不让开发被真实 `SiteID` 和 `Key` 阻塞。
- Casdoor 暂不作为主认证依赖，只作为未来多身份源或统一身份中心扩展选项。

真正对接学校登录前需要学校提供：
- `SiteID`
- `Key`
- 允许的 `ReturnURL`
- 登出回调要求
- 测试账号或测试环境
- 服务器 IP 白名单要求
- 是否允许调用 `DataCenter.asmx` 获取用户资料

## 6. 后续 AI 接手阅读顺序

后续 AI / OMX skills 接手时，优先按这个顺序阅读：

1. 本文件：`.omx/specs/ai-counselor-development-principles.md`
2. 业务阶段一 PRD：`.omx/plans/prd-ai-counselor-business-phase1.md`
3. 业务阶段一测试规格：`.omx/plans/test-spec-ai-counselor-business-phase1.md`
4. 系统定位研究：`.omx/specs/autoresearch-system-positioning/report.md`
5. NCHU SSO 调研：`.omx/specs/autoresearch-nchu-sso/report.md`
6. 技术阶段一 PRD：`.omx/plans/prd-ai-counselor-technical-phase1.md`
7. 技术阶段一测试规格：`.omx/plans/test-spec-ai-counselor-technical-phase1.md`

## 7. 执行约束

后续开发必须保持：
- 不恢复 Flask/Qdrant 为正式路线。
- 不绕过 FastAPI 业务后端。
- 不把 P2/P3 能力提前塞进 P0/P1。
- 不用不可复现的手工部署替代 Docker Compose 和文档化命令。
- 不在没有来源引用或兜底策略的情况下上线学生问答。
- 不在没有权限和审计边界的情况下处理敏感学生数据。

