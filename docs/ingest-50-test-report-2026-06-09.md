# 50 个学校文件入库与解析测试报告

测试时间：2026-06-09

## 操作记录

- 清空业务数据表，保留管理员账号。
- 从 `学校文件` 选择 50 个样本，覆盖 `.zip/.rar/.jpg/.png/.pdf/.doc/.docx/.xls/.xlsx`。
- 样本复制/硬链接到 `.cache/ingest_50` 后导入，避免 Windows 中文路径传参问题。
- 自动全流程导入时被 embedding API 401 阻断，因此后续使用 parse+chunk 专用脚本完成解析切片验收。
- 对 1 个 zip 文档额外执行了手动 `extract_archive` 流程。

## 最终统计

```text
documents: 51
parse_results: 50
chunks: 191
embeddings: 0
failed: 1
chunked: 21
parsed: 28
extracted: 1
```

说明：50 个源样本中存在重复文件，按 hash 去重后少于 50 条；zip 手动解压后新增 4 个子文档，因此最终为 51 条。

## 各类型结果

```text
.doc   parsed    25 docs, 0 chunks
.docx  chunked    2 docs, 17 chunks
.docx  failed     1 docs, 0 chunks
.jpg   chunked    1 docs, 1 chunk
.jpg   parsed     2 docs, 0 chunks
.pdf   chunked    9 docs, 136 chunks
.png   chunked    1 docs, 1 chunk
.rar   parsed     1 docs, 0 chunks
.xls   chunked    7 docs, 33 chunks
.xlsx  chunked    1 docs, 3 chunks
.zip   extracted  1 docs, 0 chunks
```

## ZIP/RAR 结论

- 支持上传 `.zip/.rar`，但默认只解析为“压缩包容器”。
- 默认不会自动解压、自动解析、自动切片内部文件。
- 现有 `extract_archive` 流程可手动触发 zip 解压导入。
- 本次 zip 内部 4 个 `.doc` 子文件已创建为子文档，但文件名编码为乱码，且旧 `.doc` 仍需转换后才能切片。
- RAR 当前只做容器占位，没有内容预览。

## 图片处理结论

- `.jpg/.png` 会走 PaddleOCR。
- 成功样本：
  - JPG：`line_count=25`，`avg_confidence=0.9082`，生成 1 个 `ocr` chunk。
  - PNG：`line_count=29`，`avg_confidence=0.9813`，生成 1 个 `ocr` chunk。
- 后续在关闭 OCR 的基线处理中，图片会标记为 `ocr_required=true`，`skip_chunking=true`，不会生成 chunk。

## PDF/OCR 结论

- 文本型 PDF 可正常解析切片。
- 扫描 PDF 在 OCR 开启时会调用 PaddleOCR，但处理较慢；本次长任务在扫描 PDF OCR 阶段超时。
- 关闭 OCR 后，扫描 PDF 会生成每页占位文本 chunk，标记 `ocr_required=true`。

## Excel 结论

- 小表完整索引。
- 大表进入受限索引，生成摘要和前 50 行样例。
- `16级开放型实验成绩.xls` 结果：
  - `row_count=11277`
  - `index_mode=sampled`
  - `indexed_row_count=50`
  - 仅生成 2 个 chunk

## 发现的问题

- Embedding API key 当前返回 401，导致全流程状态会在 embed 阶段失败。
- 上传 zip 不会自动解压处理内部文件，需要手动触发 extract 流程。
- zip 内中文文件名编码识别不可靠。
- `.doc` 旧版 Word 当前默认标记为待转换，不直接切片。
- 一个 `.docx` 失败：`Bad CRC-32 for file 'word/media/image7.png'`，需要容错跳过损坏媒体。
- OCR 对扫描 PDF 耗时较长，需要异步队列、页数预算、进度和可取消能力。
