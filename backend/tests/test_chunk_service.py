from __future__ import annotations

from pathlib import Path
import sys
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.chunk_service import ChunkService  # noqa: E402
from app.services.parse_service import ParseService  # noqa: E402


class LargeTableIndexingTests(unittest.TestCase):
    def test_large_excel_table_uses_sampled_index_and_row_chunks(self) -> None:
        parser = ParseService()
        parser.settings.table_full_index_max_rows = 5
        parser.settings.table_sample_rows = 4
        parser.settings.max_embedding_chars_per_document = 100000

        rows = [(1, ["姓名", "班级", "成绩"])]
        rows.extend((index, [f"学生{index}", "一班", str(80 + index)]) for index in range(2, 22))
        text, metadata = parser._excel_sheet_markdown(
            sheet_name="成绩",
            rows=rows,
            merged_ranges=[],
            parser="unit-test",
            sheet_index=1,
        )

        self.assertEqual(metadata["index_mode"], "sampled")
        self.assertTrue(metadata["full_index_limited"])
        self.assertEqual(metadata["row_count"], 21)
        self.assertEqual(metadata["indexed_row_count"], 4)
        self.assertIn("[大表受限索引]", text)

        chunker = ChunkService()
        chunker.rag_settings = {
            **chunker.rag_settings,
            "table_chunk_rows": 2,
            "max_document_chunks": 300,
            "max_embedding_chars_per_document": 100000,
        }
        chunks = chunker.split(text, {"sheets": [metadata]})
        table_chunks = [chunk for chunk in chunks if chunk.chunk_type == "table"]

        self.assertEqual(len(table_chunks), 2)
        self.assertTrue(all(chunk.metadata["row_count"] <= 2 for chunk in table_chunks))
        self.assertEqual(table_chunks[0].metadata["index_mode"], "sampled")

    def test_text_chunks_keep_tail_context_across_paragraph_boundaries(self) -> None:
        chunker = ChunkService()
        chunker.rag_settings = {
            **chunker.rag_settings,
            "chunk_size": 60,
            "chunk_overlap": 40,
            "max_document_chunks": 300,
            "max_embedding_chars_per_document": 100000,
        }
        text = "\n\n".join(
            [
                "2、拔河比赛",
                "活动时间：2015年5月7日下午13：30",
                "活动地点：校田径场（或室内篮球馆）",
                "参赛要求：",
                "（1）以学院为单位组成各参赛队伍。",
                "（2）每支代表队队员二十人。",
            ]
        )

        chunks = chunker.split(text)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertIn("参赛要求", chunks[1].content)
        self.assertIn("（1）以学院为单位组成各参赛队伍", chunks[1].content)


if __name__ == "__main__":
    unittest.main()
