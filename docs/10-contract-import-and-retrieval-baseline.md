# 10个合同导入与检索基线报告

记录时间：2026-06-06

## 结论

- `10个合同` 目录实际包含 11 个 PDF。
- 本轮可检索索引为 11 份 indexed 文档，active chunk 与 embedding 均为 619。
- `江西省总工会12351服务职工热线展示分析系统服务项目.pdf` 与历史 `sample_contract.pdf` hash 相同，按去重逻辑未重复创建；当前以 `sample_contract.pdf` 参与检索。
- 另有 1 条历史 `sample_contract.pdf` parsed 残留记录，无 chunk、无 embedding，不参与检索。
- 41 条合同检索 bad case 基线：严格通过 32/41，top3 文档命中 39/41，引用可用率 41/41。

## 导入状态

| 文档 | 状态 | 页数 | 文本字符 | chunks | embeddings |
| --- | --- | ---: | ---: | ---: | ---: |
| sample_contract.pdf | parsed | 4 | 3887 | 0 | 0 |
| sample_contract.pdf | indexed | 4 | 3887 | 6 | 6 |
| 2025年江西省应急管理厅智慧应急建设项目（钢铝风险监测子系统）.pdf | indexed | 58 | 59188 | 96 | 96 |
| 2025年生态环境大数据平台提升项目生态环境数据资源中心（二期）子项目技术服务合同.pdf | indexed | 26 | 25316 | 41 | 41 |
| 2026年江西倬云数据有限公司001硬件采购项目合同书.pdf | indexed | 26 | 22754 | 28 | 28 |
| 2026年江西外语外贸职业学院学生校园网络运营单位系统集成采购项目系统集成合同.pdf | indexed | 33 | 41072 | 66 | 66 |
| 2026年江西钨业控股集团有限公司用友ERP公有云服务合同.pdf | indexed | 23 | 27857 | 44 | 44 |
| 南昌大学第一附属医院互联网医院二期+智护一附系统建设项目.pdf | indexed | 169 | 126680 | 192 | 192 |
| 南昌市产业投资集团有限公司2025年下半年数字化转型（一期）项目合同书(OCR).pdf | indexed | 52 | 36313 | 73 | 73 |
| 数据流通交易平台二期建设项目.pdf | indexed | 20 | 25748 | 39 | 39 |
| 江西省林科院林业博物馆预约小程序及配套终端项目.pdf | indexed | 8 | 5742 | 8 | 8 |
| 江西诚乡关于南丰县城市公共供水管网漏损治理项目EPC总承包-智慧水务建设工程的采购项目.pdf | indexed | 12 | 15491 | 26 | 26 |

## 基线指标

评测只看检索证据，不看生成答案。

| 指标 | 结果 |
| --- | ---: |
| bad case 总数 | 41 |
| 严格通过 | 32/41, 78.05% |
| top1 文档命中 | 36/41, 87.80% |
| top3 文档命中 | 39/41, 95.12% |
| 期望关键词命中 | 34/41, 82.93% |
| 页码命中 | 36/41, 87.80% |
| 章节命中 | 38/41, 92.68% |
| 引用文档命中 | 39/41, 95.12% |
| 引用可用 | 41/41, 100.00% |
| QA 抢 top1 | 0/41 |

评测文件：

- bad case 集：[retrieval-badcases-contracts.json](retrieval-badcases-contracts.json)
- 最新 JSON 结果：[retrieval-baseline-latest.json](retrieval-baseline-latest.json)
- 最新 Markdown 结果：[retrieval-baseline-latest.md](retrieval-baseline-latest.md)
- 运行脚本：[../scripts/run-contract-retrieval-baseline.py](../scripts/run-contract-retrieval-baseline.py)

## 剩余失败类型

- 目标文档已命中，但具体证据页未进入 top5：`campus_total`、`campus_payment`、`erp_data_retention`。
- chunk 章节边界不够准，导致正确内容缺上一页/上一段标题：`ecology_total`。
- OCR 文档文本质量导致项目名和条款语义弱匹配：`ocr_confidentiality`、`ocr_dispute`。
- 通用意图仍会被类似条款干扰：`emergency_payment`、`data_ip`、`union_effective`。

## 本轮修复

- 修复 DashScope embedding 批量大小：新增 `embedding_batch_size=10`，避免一次提交超过 10 条文本。
- `ModelService.embed()` 内部按配置拆批，`DocumentPipeline` 使用相同批大小。
- 批量导入脚本去重时优先匹配 indexed 文档，避免重复 hash 命中历史 parsed 残留。
- 检索 keyword 召回纳入文档标题、文件名、正文，并对去空白文本做匹配。
- 查询词抽取增加合同领域意图词和项目名片段。
- rerank 前候选从 `top_k * 4` 扩大到至少 40。
- 本地 rerank 提高文档名命中权重，降低 QA 对明确文档问题的干扰。
