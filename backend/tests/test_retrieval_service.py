from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.retrieval_service import RetrievalService  # noqa: E402


def _item(source: str, index: int) -> dict:
    return {
        "chunk_id": f"{source}-{index}",
        "document_id": f"00000000-0000-0000-0000-0000000000{index:02d}",
        "document_title": f"文档{index}",
        "document_name": f"doc-{index}.pdf",
        "content": f"测试内容 {source} {index}",
        "section_path": "测试章节",
        "page_start": index,
        "url": f"http://example.local/{source}/{index}",
        "source": source,
        "score": 1.0,
    }


def _corpus_version() -> dict:
    return {
        "document_count": 2,
        "latest_document_update": "2026-06-23 00:00:00+00:00",
        "knowledge_base_version": 1,
        "latest_knowledge_update": "2026-06-23 00:00:00+00:00",
    }


class RetrievalServiceParameterTests(unittest.IsolatedAsyncioTestCase):
    async def test_top_k_controls_recall_and_rerank_top_k_controls_final_context(self) -> None:
        service = RetrievalService()
        service.rag_settings = {
            "vector_top_k": 30,
            "keyword_top_k": 30,
            "qa_top_k": 10,
            "rerank_top_k": 5,
            "rerank_max_candidates": 10,
            "rerank_enabled": False,
            "similarity_threshold": 0,
            "rerank_threshold": 0,
        }
        service._get_cached_retrieval = AsyncMock(return_value=None)
        service._set_cached_retrieval = AsyncMock()
        service._corpus_version = AsyncMock(return_value=_corpus_version())

        calls: dict[str, int] = {}

        async def vector_search(db, query, top_k, document_ids=None):
            calls["vector"] = top_k
            return [_item("vector", index) for index in range(1, top_k + 1)]

        async def keyword_search(db, query, top_k, document_ids=None):
            calls["keyword"] = top_k
            return [_item("keyword", index) for index in range(1, top_k + 1)]

        async def qa_search(db, query, top_k, document_ids=None):
            calls["qa"] = top_k
            return [_item("qa", index) for index in range(1, top_k + 1)]

        async def rerank(query, candidates):
            calls["rerank_candidates"] = len(candidates)
            return candidates

        service._vector_search = vector_search
        service._keyword_search = keyword_search
        service._qa_search = qa_search
        service._rerank = rerank

        result = await service.search(
            db=None,
            query="测试问题",
            top_k=4,
            rerank_top_k=2,
            enable_qa_recall=False,
        )

        self.assertEqual(calls["vector"], 4)
        self.assertEqual(calls["keyword"], 4)
        self.assertNotIn("qa", calls)
        self.assertEqual(calls["rerank_candidates"], 8)
        self.assertEqual(len(result["final_context"]), 2)
        self.assertEqual(result["retrieval_options"]["effective_vector_top_k"], 4)
        self.assertEqual(result["retrieval_options"]["effective_keyword_top_k"], 4)
        self.assertEqual(result["retrieval_options"]["effective_final_top_k"], 2)
        self.assertFalse(result["retrieval_options"]["enable_qa_recall"])

    async def test_low_confidence_candidates_do_not_become_answer_context(self) -> None:
        service = RetrievalService()
        service.rag_settings = {
            "vector_top_k": 30,
            "keyword_top_k": 30,
            "qa_top_k": 10,
            "rerank_top_k": 5,
            "rerank_max_candidates": 10,
            "rerank_enabled": False,
            "similarity_threshold": 0.35,
            "rerank_threshold": 0.45,
        }
        service._get_cached_retrieval = AsyncMock(return_value=None)
        service._set_cached_retrieval = AsyncMock()
        service._corpus_version = AsyncMock(return_value=_corpus_version())

        async def vector_search(db, query, top_k, document_ids=None):
            return [{**_item("vector", 1), "score": 0.05}]

        async def empty_search(db, query, top_k, document_ids=None):
            return []

        async def rerank(query, candidates):
            return candidates

        service._vector_search = vector_search
        service._keyword_search = empty_search
        service._qa_search = empty_search
        service._rerank = rerank

        result = await service.search(db=None, query="unmatched question", rerank_top_k=5)

        self.assertEqual(result["rerank_results"], [])
        self.assertEqual(result["final_context"], [])
        self.assertEqual(result["answer_context"], [])
        self.assertEqual(result["citations"], [])

    async def test_school_query_terms_extract_activity_and_requirement_terms(self) -> None:
        service = RetrievalService()

        terms = service._query_terms("拔河比赛什么时候开始，参赛要求是什么")

        self.assertIn("拔河比赛", terms)
        self.assertIn("参赛要求", terms)

    async def test_requirement_heading_triggers_adjacent_context_expansion(self) -> None:
        service = RetrievalService()

        self.assertTrue(
            service._should_expand_adjacent_context(
                "拔河比赛什么时候开始，参赛要求是什么",
                {"content": "2、拔河比赛\n\n活动时间：2015年5月7日下午13：30\n\n参赛要求："},
            )
        )

    async def test_school_activity_query_penalizes_unrelated_qa(self) -> None:
        service = RetrievalService()
        terms = service._query_terms("拔河比赛什么时候开始，参赛要求是什么")

        penalty = service._qa_mismatch_penalty(
            "拔河比赛什么时候开始，参赛要求是什么",
            {"source": "qa_vector"},
            terms,
            "合同争议解决方式是什么双方协商不成向法院起诉",
        )

        self.assertGreater(penalty, 0)

    async def test_scholarship_query_filters_travel_documents_from_context_and_citations(self) -> None:
        service = RetrievalService()
        service.rag_settings = {
            "vector_top_k": 30,
            "keyword_top_k": 30,
            "qa_top_k": 10,
            "rerank_top_k": 5,
            "rerank_max_candidates": 10,
            "rerank_enabled": False,
            "similarity_threshold": 0,
            "rerank_threshold": 0,
        }
        service._get_cached_retrieval = AsyncMock(return_value=None)
        service._set_cached_retrieval = AsyncMock()
        service._corpus_version = AsyncMock(return_value=_corpus_version())

        async def vector_search(db, query, top_k, document_ids=None):
            return [
                {
                    **_item("vector", 1),
                    "document_title": "奖学金申报说明文档",
                    "content": "国家奖学金申请材料包括申请表、成绩证明、家庭经济困难说明等。",
                },
                {
                    **_item("vector", 2),
                    "document_title": "网上差旅审批操作手册",
                    "content": "差旅审批、出差申请、住宿费和交通费报销流程。",
                },
            ]

        async def empty_search(db, query, top_k, document_ids=None):
            return []

        async def rerank(query, candidates):
            return candidates

        service._vector_search = vector_search
        service._keyword_search = empty_search
        service._qa_search = empty_search
        service._rerank = rerank

        result = await service.search(db=None, query="申请奖学金需要准备哪些材料", rerank_top_k=5)

        self.assertEqual(result["retrieval_options"]["business_domain"]["domain"], "scholarship_aid")
        self.assertTrue(result["business_filter"]["enabled"])
        self.assertGreater(result["business_filter"]["removed_total"], 0)
        self.assertTrue(result["answer_context"])
        self.assertTrue(all("差旅" not in item["document_title"] for item in result["answer_context"]))
        self.assertTrue(all("差旅" not in item["document_title"] for item in result["citations"]))

    async def test_followup_query_uses_context_domain_to_filter_unrelated_documents(self) -> None:
        service = RetrievalService()
        service.rag_settings = {
            "vector_top_k": 30,
            "keyword_top_k": 30,
            "qa_top_k": 10,
            "rerank_top_k": 5,
            "rerank_max_candidates": 10,
            "rerank_enabled": False,
            "similarity_threshold": 0,
            "rerank_threshold": 0,
        }
        service._get_cached_retrieval = AsyncMock(return_value=None)
        service._set_cached_retrieval = AsyncMock()
        service._corpus_version = AsyncMock(return_value=_corpus_version())

        async def vector_search(db, query, top_k, document_ids=None):
            return [
                {
                    **_item("vector", 1),
                    "document_title": "奖学金申报说明文档",
                    "document_name": "奖学金申报说明文档.pdf",
                    "content": "国家奖学金申请材料包括申请表、成绩证明、家庭经济困难说明等。",
                },
                {
                    **_item("vector", 2),
                    "document_title": "网上差旅审批操作手册",
                    "document_name": "网上差旅审批操作手册.pdf",
                    "content": "差旅审批、出差申请、住宿费和交通费报销流程。",
                },
            ]

        async def empty_search(db, query, top_k, document_ids=None):
            return []

        async def rerank(query, candidates):
            return candidates

        service._vector_search = vector_search
        service._keyword_search = empty_search
        service._qa_search = empty_search
        service._rerank = rerank

        result = await service.search(
            db=None,
            query="还需要哪些材料",
            rerank_top_k=5,
            context_constraints={
                "is_followup": True,
                "intent": "followup",
                "active_topic": "奖学金申请政策",
                "user_goal": "梳理奖学金申请条件和材料",
                "target_documents": ["奖学金申报说明文档.pdf"],
                "constraint_strength": "strict",
            },
        )

        self.assertEqual(result["retrieval_options"]["business_domain"]["domain"], "scholarship_aid")
        self.assertTrue(result["context_constraint_filter"]["enabled"])
        self.assertTrue(result["answer_context"])
        self.assertTrue(all("奖学金" in item["document_title"] for item in result["answer_context"]))
        self.assertTrue(all("差旅" not in item["document_title"] for item in result["citations"]))

    async def test_travel_query_keeps_travel_documents(self) -> None:
        service = RetrievalService()
        query_domain = service._classify_business_domain("差旅报销审批流程是什么")
        candidates = [
            {
                **_item("keyword", 1),
                "document_title": "网上差旅审批操作手册",
                "content": "差旅审批、出差申请、住宿费和交通费报销流程。",
            },
            {
                **_item("keyword", 2),
                "document_title": "奖学金申报说明文档",
                "content": "奖学金、助学金、家庭经济困难认定申请材料。",
            },
        ]

        filtered, stats = service._filter_by_business_domain(query_domain, candidates, stage="context")

        self.assertTrue(stats["enabled"])
        self.assertEqual(len(filtered), 1)
        self.assertIn("差旅", filtered[0]["document_title"])

    async def test_general_query_does_not_enable_business_filter(self) -> None:
        service = RetrievalService()
        query_domain = service._classify_business_domain("学校有哪些办事流程")

        filtered, stats = service._filter_by_business_domain(query_domain, [_item("keyword", 1)], stage="context")

        self.assertFalse(stats["enabled"])
        self.assertEqual(len(filtered), 1)

    async def test_legacy_encoded_document_sources_are_filtered_from_answer_and_citations(self) -> None:
        service = RetrievalService()
        service.rag_settings = {
            "vector_top_k": 30,
            "keyword_top_k": 30,
            "qa_top_k": 10,
            "rerank_top_k": 5,
            "rerank_max_candidates": 10,
            "rerank_enabled": False,
            "similarity_threshold": 0,
            "rerank_threshold": 0,
        }
        service._get_cached_retrieval = AsyncMock(return_value=None)
        service._set_cached_retrieval = AsyncMock()
        service._corpus_version = AsyncMock(return_value=_corpus_version())

        async def vector_search(db, query, top_k, document_ids=None):
            return [
                {
                    **_item("vector", 1),
                    "document_title": "%bd%93%e8%82%b2%e6%96%87%e4%bb%b6.doc",
                    "document_name": "%bd%93%e8%82%b2%e6%96%87%e4%bb%b6.doc",
                    "content": "legacy encoded document content",
                },
                {
                    **_item("vector", 2),
                    "document_title": "student handbook",
                    "document_name": "student-handbook.pdf",
                    "content": "sports venue fee policy for students",
                },
            ]

        async def empty_search(db, query, top_k, document_ids=None):
            return []

        async def rerank(query, candidates):
            return candidates

        service._vector_search = vector_search
        service._keyword_search = empty_search
        service._qa_search = empty_search
        service._rerank = rerank

        result = await service.search(db=None, query="sports venue fee", rerank_top_k=5)

        self.assertTrue(result["answer_context"])
        self.assertTrue(all("%bd%93" not in item["document_title"] for item in result["answer_context"]))
        self.assertTrue(all("%bd%93" not in item["document_title"] for item in result["citations"]))

    async def test_citations_skip_legacy_encoded_document_sources(self) -> None:
        service = RetrievalService()
        citations = service._citations(
            [
                {
                    **_item("keyword", 1),
                    "document_title": "%bd%93%e8%82%b2%e6%96%87%e4%bb%b6.doc",
                    "document_name": "%bd%93%e8%82%b2%e6%96%87%e4%bb%b6.doc",
                },
                {
                    **_item("keyword", 2),
                    "document_title": "student handbook",
                    "document_name": "student-handbook.pdf",
                },
            ]
        )

        self.assertEqual(len(citations), 1)
        self.assertNotIn("%bd%93", citations[0]["document_title"])

    async def test_internal_documents_are_filtered_from_answer_and_citations(self) -> None:
        service = RetrievalService()
        service.rag_settings = {
            "vector_top_k": 30,
            "keyword_top_k": 30,
            "qa_top_k": 10,
            "rerank_top_k": 5,
            "rerank_max_candidates": 10,
            "rerank_enabled": False,
            "similarity_threshold": 0,
            "rerank_threshold": 0,
        }
        service._get_cached_retrieval = AsyncMock(return_value=None)
        service._set_cached_retrieval = AsyncMock()
        service._corpus_version = AsyncMock(return_value=_corpus_version())

        async def vector_search(db, query, top_k, document_ids=None):
            return [
                {
                    **_item("vector", 1),
                    "document_title": "接口测试文档-2026-06-12",
                    "document_name": "接口测试文档-2026-06-12.md",
                    "content": "POST /api/v1/chat/stream internal API test cases",
                },
                {
                    **_item("vector", 2),
                    "document_title": "学生手册",
                    "document_name": "学生手册.pdf",
                    "content": "学生办事指南和校方公开政策说明",
                },
            ]

        async def empty_search(db, query, top_k, document_ids=None):
            return []

        async def rerank(query, candidates):
            return candidates

        service._vector_search = vector_search
        service._keyword_search = empty_search
        service._qa_search = empty_search
        service._rerank = rerank

        result = await service.search(db=None, query="学生办事指南", rerank_top_k=5)

        self.assertTrue(result["answer_context"])
        self.assertTrue(all("接口测试" not in item["document_title"] for item in result["answer_context"]))
        self.assertTrue(all("接口测试" not in item["document_title"] for item in result["citations"]))

    async def test_citations_skip_internal_documents(self) -> None:
        service = RetrievalService()
        citations = service._citations(
            [
                {
                    **_item("keyword", 1),
                    "document_title": "API接口设计",
                    "document_name": "API接口设计.md",
                },
                {
                    **_item("keyword", 2),
                    "document_title": "官方办事指南",
                    "document_name": "官方办事指南.pdf",
                },
            ]
        )

        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]["document_title"], "官方办事指南")

    async def test_direct_qa_normalized_text_matching(self) -> None:
        service = RetrievalService()

        self.assertEqual(
            service._normalize_direct_qa_text("申请奖学金需要准备哪些材料？"),
            service._normalize_direct_qa_text("申请 奖学金 需要准备哪些材料"),
        )
        self.assertEqual(
            service._direct_qa_text_similarity("申请奖学金需要准备哪些材料", "申请奖学金需要准备哪些材料"),
            1.0,
        )

    async def test_direct_qa_rejects_conflicting_business_domain(self) -> None:
        service = RetrievalService()
        query_domain = service._classify_business_domain("申请奖学金需要准备哪些材料")
        item = service._annotate_business_domain(
            {
                "document_title": "网上差旅审批操作手册",
                "content": "差旅审批、出差申请、住宿费和交通费报销流程。",
            }
        )

        self.assertFalse(service._qa_domain_allowed(query_domain, item))

    async def test_policy_coverage_supplements_missing_transfer_facets(self) -> None:
        service = RetrievalService()
        initial = [
            {
                **_item("keyword", 1),
                "document_title": "普通高等学校学生管理规定",
                "content": "学生申请转学，应当说明理由，经所在学校和拟转入学校同意。",
            }
        ]
        supplements = [
            {
                **_item("keyword", 2),
                "document_title": "普通高等学校学生管理规定",
                "content": "有下列情形之一，不得转学：入学未满一学期或者毕业前一年等六类情形。",
            },
            {
                **_item("keyword", 3),
                "document_title": "普通高等学校学生管理规定",
                "content": "因学校培养条件改变等非个人原因需要转学的，由学校出具证明，省级教育行政部门协调。",
            },
            {
                **_item("keyword", 4),
                "document_title": "普通高等学校学生管理规定",
                "content": "学校应当及时公示转学情况，转学完成后3个月内报所在地省级教育行政部门备案。",
            },
            {
                **_item("keyword", 5),
                "document_title": "普通高等学校学生管理规定",
                "content": "跨省转学涉及户口迁移的，转入地省级教育行政部门将材料抄送公安机关。",
            },
        ]

        async def keyword_search(db, query, top_k, document_ids=None):
            return supplements

        service._keyword_search = keyword_search
        query = "转学需要准备什么"
        coverage = service._policy_coverage_plan(query, initial)
        expanded, updated = await service._complete_policy_context(
            db=object(),
            query=query,
            contexts=initial,
            query_domain=service._classify_business_domain(query),
            coverage=coverage,
        )

        self.assertTrue(updated["enabled"])
        self.assertIn("restrictions", updated["covered_facets"])
        self.assertIn("special_cases", updated["covered_facets"])
        self.assertIn("post_requirements", updated["covered_facets"])
        self.assertIn("cross_department", updated["covered_facets"])
        self.assertGreater(len(expanded), len(initial))

    async def test_non_policy_query_does_not_enable_policy_coverage(self) -> None:
        service = RetrievalService()

        coverage = service._policy_coverage_plan("学校在哪里", [_item("keyword", 1)])

        self.assertFalse(coverage["enabled"])

    async def test_citations_merge_same_document_and_hide_evidence(self) -> None:
        service = RetrievalService()
        contexts = [
            {
                **_item("keyword", 1),
                "document_id": "00000000-0000-0000-0000-000000000001",
                "chunk_id": "00000000-0000-0000-0000-000000000101",
                "content": "转学申请应当说明理由，经所在学校和拟转入学校同意后办理。",
                "page_start": 3,
                "section_path": "转学管理 表格 1",
            },
            {
                **_item("keyword", 2),
                "document_id": "00000000-0000-0000-0000-000000000001",
                "chunk_id": "00000000-0000-0000-0000-000000000102",
                "content": "转学完成后3个月内，由转入学校报所在地省级教育行政部门备案。",
                "page_start": 4,
                "section_path": "转学管理 表格 2",
            },
        ]

        citations = service._citations(contexts, query="转学备案时间", answer="转学完成后3个月内备案。")

        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]["chunk_id"], "00000000-0000-0000-0000-000000000101")
        self.assertEqual(citations[0]["page_numbers"], [3, 4])
        self.assertEqual(citations[0]["table_numbers"], ["表格 1", "表格 2"])
        self.assertEqual(citations[0]["location_label"], "第 3-4 页，表格 1、表格 2")
        self.assertNotIn("evidence", citations[0])

    async def test_citations_location_label_uses_page_ranges(self) -> None:
        service = RetrievalService()
        item = {
            **_item("keyword", 1),
            "page_start": 7,
            "page_end": 8,
            "section_path": "办理说明",
        }

        citations = service._citations([item], query="转学备案时间", answer="3个月内备案")

        self.assertEqual(citations[0]["page_numbers"], [7, 8])
        self.assertEqual(citations[0]["section_paths"], ["办理说明"])
        self.assertEqual(citations[0]["location_label"], "第 7-8 页")


if __name__ == "__main__":
    unittest.main()
