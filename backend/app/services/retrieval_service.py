import hashlib
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.json_utils import to_jsonable
from app.db.session import AsyncSessionLocal
from app.services.minio_service import MinioService
from app.services.model_service import ModelService
from app.services.rag_settings_service import RagSettingsService
from app.services.redis_service import RedisService
from app.services.rerank_service import RerankService


class RetrievalService:
    MAX_ANSWER_CONTEXT_DOCS = 2
    MAX_ANSWER_CONTEXT_CHUNKS = 4
    MAX_CITATION_DOCS = 2
    MAX_CITATION_ITEMS = 3
    CITATION_EVIDENCE_CHARS = 240
    LEGACY_URL_ENCODED_NAME_PATTERN = r"(^|[^%])%(8[0-9A-F]|9[0-9A-F]|A[0-9A-F]|B[0-9A-F])(%[0-9A-F]{2}){2,}|%EF%BF%BD"
    LEGACY_URL_ENCODED_NAME_RE = re.compile(LEGACY_URL_ENCODED_NAME_PATTERN, re.IGNORECASE)
    DEFAULT_BLACKLIST_KEYWORDS = (
        "接口测试",
        "API接口",
        "API 接口",
        "接口设计",
        "测试文档",
        "内部文档",
        "内部资料",
        "涉密",
        "保密",
        "AI底座",
        "底座规划",
    )

    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_service = ModelService()
        self.rerank_service = RerankService()
        self.redis_service = RedisService()
        self.rag_settings = RagSettingsService().get_effective()
        self.minio_service = MinioService()
        self.blacklist_keywords = self._load_blacklist_keywords()

    async def search(
        self,
        db: AsyncSession,
        query: str,
        top_k: int | None = None,
        rerank_top_k: int | None = None,
        document_ids: list[str] | None = None,
        enable_vector_recall: bool = True,
        enable_keyword_recall: bool = True,
        enable_qa_recall: bool = True,
        context_constraints: dict | None = None,
    ) -> dict:
        constraints = self._normalize_context_constraints(context_constraints)
        vector_top_k = self._limit(
            top_k if top_k is not None else self.rag_settings["vector_top_k"],
            fallback=int(self.rag_settings["vector_top_k"]),
            max_value=100,
        )
        keyword_top_k = self._limit(
            top_k if top_k is not None else self.rag_settings["keyword_top_k"],
            fallback=int(self.rag_settings["keyword_top_k"]),
            max_value=100,
        )
        qa_top_k = self._limit(
            top_k if top_k is not None else self.rag_settings["qa_top_k"],
            fallback=int(self.rag_settings["qa_top_k"]),
            max_value=100,
        )
        final_top_k = self._limit(
            rerank_top_k if rerank_top_k is not None else self.rag_settings["rerank_top_k"],
            fallback=int(self.rag_settings["rerank_top_k"]),
            max_value=50,
        )
        options = {
            "top_k": top_k,
            "rerank_top_k": rerank_top_k,
            "effective_vector_top_k": vector_top_k,
            "effective_keyword_top_k": keyword_top_k,
            "effective_qa_top_k": qa_top_k,
            "effective_final_top_k": final_top_k,
            "document_ids": document_ids or None,
            "enable_vector_recall": enable_vector_recall,
            "enable_keyword_recall": enable_keyword_recall,
            "enable_qa_recall": enable_qa_recall,
            "context_constraints": constraints or None,
        }
        query_domain = self._classify_query_business_domain(query, constraints)
        options["business_domain"] = query_domain
        corpus_version = await self._corpus_version(db)
        options["corpus_version"] = corpus_version
        cached = await self._get_cached_retrieval(
            query,
            final_top_k,
            options,
            corpus_version=corpus_version,
        )
        if cached:
            return cached

        vector_results = (
            await self._vector_search(db, query, top_k=vector_top_k, document_ids=document_ids)
            if enable_vector_recall
            else []
        )
        vector_results = self._filter_invalid_document_sources(vector_results, stage="vector")
        keyword_results = (
            await self._keyword_search(db, query, top_k=keyword_top_k, document_ids=document_ids)
            if enable_keyword_recall
            else []
        )
        keyword_results = self._filter_invalid_document_sources(keyword_results, stage="keyword")
        qa_results = (
            await self._qa_search(db, query, top_k=qa_top_k, document_ids=document_ids)
            if enable_qa_recall
            else []
        )
        qa_results = self._filter_invalid_document_sources(qa_results, stage="qa")
        fused = self._rrf([vector_results, keyword_results, qa_results])
        fused = self._filter_invalid_document_sources(fused, stage="recall")
        fused, constraint_filter = self._apply_context_constraints(constraints, fused, stage="recall")
        fused, business_filter = self._filter_by_business_domain(query_domain, fused, stage="recall")
        rerank_candidates = fused[: self._rerank_candidate_count(final_top_k, len(fused))]
        reranked = await self._rerank(query, rerank_candidates)
        reranked = self._apply_local_rank_adjustments(query, reranked, query_domain=query_domain, context_constraints=constraints)
        reranked, constraint_rerank_filter = self._apply_context_constraints(constraints, reranked, stage="rerank")
        reranked, rerank_filter = self._filter_by_business_domain(query_domain, reranked, stage="rerank")
        reranked = self._apply_threshold_filter(reranked)
        final = reranked[:final_top_k]
        final_context = await self._expand_adjacent_context(db, query, final)
        final_context, constraint_context_filter = self._apply_context_constraints(constraints, final_context, stage="context")
        final_context, context_filter = self._filter_by_business_domain(query_domain, final_context, stage="context")
        policy_coverage = self._policy_coverage_plan(query, final_context)
        if policy_coverage["enabled"]:
            final_context, policy_coverage = await self._complete_policy_context(
                db,
                query,
                final_context,
                query_domain,
                policy_coverage,
            )
        final_context = self._filter_invalid_document_sources(final_context, stage="context")
        answer_context = self.select_answer_context(query, final_context)
        answer_context, constraint_answer_filter = self._apply_context_constraints(constraints, answer_context, stage="answer_context")
        answer_context, answer_filter = self._filter_by_business_domain(query_domain, answer_context, stage="answer_context")
        answer_context = self._filter_invalid_document_sources(answer_context, stage="answer_context")
        citations = self._citations(answer_context)
        result = to_jsonable({
            "raw_query": query,
            "rewritten_query": query,
            "recall_results": vector_results + keyword_results + qa_results,
            "rerank_results": final,
            "final_context": final_context,
            "answer_context": answer_context,
            "citations": citations,
            "business_filter": self._merge_business_filter_stats(
                business_filter,
                rerank_filter,
                context_filter,
                answer_filter,
            ),
            "context_constraint_filter": self._merge_context_constraint_stats(
                constraint_filter,
                constraint_rerank_filter,
                constraint_context_filter,
                constraint_answer_filter,
            ),
            "policy_coverage": policy_coverage,
            "retrieval_options": options,
            "effective_settings": self.rag_settings,
            "corpus_version": corpus_version,
        })
        await self._set_cached_retrieval(
            query,
            final_top_k,
            options,
            result,
            corpus_version=corpus_version,
        )
        return result

    async def find_direct_qa_answer(
        self,
        db: AsyncSession,
        query: str,
        document_ids: list[str] | None = None,
        context_constraints: dict | None = None,
    ) -> dict | None:
        clean_query = query.strip()
        if not clean_query or db is None:
            return None
        constraints = self._normalize_context_constraints(context_constraints)
        query_domain = self._classify_query_business_domain(clean_query, constraints)
        exact_hit = await self._find_exact_qa_hit(db, clean_query, query_domain, document_ids)
        if exact_hit and not self._is_invalid_document_source(exact_hit):
            return exact_hit
        semantic_hit = await self._find_semantic_qa_hit(db, clean_query, query_domain, document_ids)
        if semantic_hit and not self._is_invalid_document_source(semantic_hit):
            return semantic_hit
        return None

    async def _find_exact_qa_hit(
        self,
        db: AsyncSession,
        query: str,
        query_domain: dict,
        document_ids: list[str] | None,
    ) -> dict | None:
        rows = await db.execute(
            text(
                f"""
                SELECT q.id AS qa_pair_id, q.question AS qa_question, q.answer AS qa_answer,
                       q.source_document_id AS document_id,
                       d.title AS document_title, d.file_name AS document_name,
                       NULL::integer AS page_start, NULL::integer AS page_end,
                       'QA问答对' AS section_path,
                       q.source_url AS qa_source_url,
                       d.source_url, d.preview_url, d.download_url,
                       d.storage_bucket, d.storage_object_key,
                       q.tags,
                       COALESCE(q.source_url, d.source_url, d.preview_url, d.download_url) AS url,
                       similarity(q.question, :query) AS score
                FROM qa_pairs q
                LEFT JOIN documents d ON d.id = q.source_document_id
                WHERE q.status = 'enabled'
                  AND q.deleted_at IS NULL
                  AND q.question IS NOT NULL
                  AND q.answer IS NOT NULL
                  AND btrim(q.question) <> ''
                  AND btrim(q.answer) <> ''
                  AND (
                    q.source_document_id IS NULL
                    OR (
                      d.deleted_at IS NULL
                      AND d.file_name !~* :legacy_url_encoded_name_pattern
                      AND NOT ({self._document_blacklist_sql()})
                    )
                  )
                  AND (:document_ids_is_null OR q.source_document_id = ANY(CAST(:document_ids AS uuid[])))
                  AND (
                    q.question ILIKE :keyword
                    OR similarity(q.question, :query) >= 0.74
                  )
                ORDER BY similarity(q.question, :query) DESC, q.updated_at DESC
                LIMIT 20
                """
            ),
            {
                "query": query,
                "keyword": f"%{query}%",
                "document_ids": document_ids,
                "document_ids_is_null": document_ids is None,
                "legacy_url_encoded_name_pattern": self.LEGACY_URL_ENCODED_NAME_PATTERN,
                "blacklist_keywords": self._blacklist_sql_patterns(),
            },
        )
        normalized_query = self._normalize_direct_qa_text(query)
        best: dict | None = None
        for row in rows:
            item = self._normalize_qa_direct_row(dict(row._mapping), "exact")
            if self._is_invalid_document_source(item):
                continue
            if not self._qa_domain_allowed(query_domain, item):
                continue
            normalized_question = self._normalize_direct_qa_text(str(item.get("qa_question") or ""))
            if normalized_question == normalized_query:
                item["direct_match_type"] = "exact"
                item["direct_match_score"] = 1.0
                return item
            if normalized_query and normalized_query in normalized_question:
                score = len(normalized_query) / max(1, len(normalized_question))
                if score >= 0.82 and (best is None or score > float(best.get("direct_match_score") or 0)):
                    item["direct_match_type"] = "contained"
                    item["direct_match_score"] = round(score, 4)
                    best = item
        return best

    async def _find_semantic_qa_hit(
        self,
        db: AsyncSession,
        query: str,
        query_domain: dict,
        document_ids: list[str] | None,
    ) -> dict | None:
        try:
            embedding = (await self.model_service.embed([query]))[0]
        except Exception:
            return None
        vector_literal = "[" + ",".join(str(x) for x in embedding) + "]"
        rows = await db.execute(
            text(
                f"""
                SELECT q.id AS qa_pair_id, q.question AS qa_question, q.answer AS qa_answer,
                       q.source_document_id AS document_id,
                       d.title AS document_title, d.file_name AS document_name,
                       NULL::integer AS page_start, NULL::integer AS page_end,
                       'QA问答对' AS section_path,
                       q.source_url AS qa_source_url,
                       d.source_url, d.preview_url, d.download_url,
                       d.storage_bucket, d.storage_object_key,
                       q.tags,
                       COALESCE(q.source_url, d.source_url, d.preview_url, d.download_url) AS url,
                       1 - (qe.embedding <=> CAST(:embedding AS vector)) AS score
                FROM qa_pair_embeddings qe
                JOIN qa_pairs q ON q.id = qe.qa_pair_id
                LEFT JOIN documents d ON d.id = q.source_document_id
                WHERE q.status = 'enabled'
                  AND q.deleted_at IS NULL
                  AND q.question IS NOT NULL
                  AND q.answer IS NOT NULL
                  AND btrim(q.question) <> ''
                  AND btrim(q.answer) <> ''
                  AND (
                    q.source_document_id IS NULL
                    OR (
                      d.deleted_at IS NULL
                      AND d.file_name !~* :legacy_url_encoded_name_pattern
                      AND NOT ({self._document_blacklist_sql()})
                    )
                  )
                  AND (:document_ids_is_null OR q.source_document_id = ANY(CAST(:document_ids AS uuid[])))
                ORDER BY qe.embedding <=> CAST(:embedding AS vector)
                LIMIT 8
                """
            ),
            {
                "embedding": vector_literal,
                "document_ids": document_ids,
                "document_ids_is_null": document_ids is None,
                "legacy_url_encoded_name_pattern": self.LEGACY_URL_ENCODED_NAME_PATTERN,
                "blacklist_keywords": self._blacklist_sql_patterns(),
            },
        )
        for row in rows:
            item = self._normalize_qa_direct_row(dict(row._mapping), "semantic")
            if self._is_invalid_document_source(item):
                continue
            score = float(item.get("score") or 0)
            lexical_score = self._direct_qa_text_similarity(query, str(item.get("qa_question") or ""))
            if not self._qa_domain_allowed(query_domain, item):
                continue
            if score >= 0.88 or (score >= 0.84 and lexical_score >= 0.82):
                item["direct_match_type"] = "semantic"
                item["direct_match_score"] = round(max(score, lexical_score), 4)
                item["direct_vector_score"] = round(score, 4)
                item["direct_text_score"] = round(lexical_score, 4)
                return item
        return None

    def _normalize_qa_direct_row(self, item: dict, source: str) -> dict:
        qa_question = str(item.get("qa_question") or "")
        qa_answer = str(item.get("qa_answer") or "")
        normalized = self._normalize_result(
            {
                **item,
                "source": f"qa_direct_{source}",
                "content": f"{qa_question}\n{qa_answer}".strip(),
            }
        )
        normalized["qa_question"] = qa_question
        normalized["qa_answer"] = qa_answer
        return self._annotate_business_domain(normalized)

    def _qa_domain_allowed(self, query_domain: dict, item: dict) -> bool:
        domain = str(query_domain.get("domain") or "general")
        confidence = float(query_domain.get("confidence") or 0)
        if domain == "general" or confidence < 0.62:
            return True
        item_domain = str(item.get("business_domain") or "general")
        item_confidence = float(item.get("business_domain_confidence") or 0)
        return self._business_domain_matches(domain, item_domain, item_confidence)

    def _normalize_direct_qa_text(self, text: str) -> str:
        return re.sub(r"[\s\W_]+", "", text.lower())

    def _direct_qa_text_similarity(self, query: str, candidate: str) -> float:
        left = self._normalize_direct_qa_text(query)
        right = self._normalize_direct_qa_text(candidate)
        if not left or not right:
            return 0.0
        if left == right:
            return 1.0
        if left in right or right in left:
            return min(len(left), len(right)) / max(len(left), len(right))
        left_terms = set(self._meaningful_query_terms(query))
        right_terms = set(self._meaningful_query_terms(candidate))
        if not left_terms or not right_terms:
            return 0.0
        return len(left_terms & right_terms) / len(left_terms | right_terms)

    async def _vector_search(
        self, db: AsyncSession, query: str, top_k: int, document_ids: list[str] | None = None
    ) -> list[dict]:
        try:
            embedding = (await self.model_service.embed([query]))[0]
        except Exception:
            return []
        vector_literal = "[" + ",".join(str(x) for x in embedding) + "]"
        rows = await db.execute(
            text(
                f"""
                SELECT c.id AS chunk_id, c.document_id, d.title AS document_title,
                       d.file_name AS document_name,
                       c.content, c.page_start, c.page_end, c.section_path,
                       c.metadata AS metadata,
                       d.source_url, d.preview_url, d.download_url,
                       d.storage_bucket, d.storage_object_key,
                       COALESCE(d.source_url, d.preview_url, d.download_url) AS url,
                       1 - (e.embedding <=> CAST(:embedding AS vector)) AS score
                FROM chunk_embeddings e
                JOIN document_chunks c ON c.id = e.chunk_id
                JOIN documents d ON d.id = c.document_id
                WHERE c.is_active = true
                  AND d.deleted_at IS NULL
                  AND d.file_name !~* :legacy_url_encoded_name_pattern
                  AND NOT ({self._document_blacklist_sql()})
                  AND (:document_ids_is_null OR d.id = ANY(CAST(:document_ids AS uuid[])))
                ORDER BY e.embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
                """
            ),
            {
                "embedding": vector_literal,
                "top_k": top_k,
                "document_ids": document_ids,
                "document_ids_is_null": document_ids is None,
                "legacy_url_encoded_name_pattern": self.LEGACY_URL_ENCODED_NAME_PATTERN,
                "blacklist_keywords": self._blacklist_sql_patterns(),
            },
        )
        return [self._normalize_result({**dict(row._mapping), "source": "vector"}) for row in rows]

    async def _keyword_search(
        self, db: AsyncSession, query: str, top_k: int, document_ids: list[str] | None = None
    ) -> list[dict]:
        terms = self._query_terms(query)
        project_terms = set(
            self._project_terms_from_query(
                self._normalize_query_text(query),
                self._ranking_marker_candidates(),
            )
        )
        params = {
            "query": query,
            "top_k": top_k,
            "document_ids": document_ids,
            "document_ids_is_null": document_ids is None,
            "legacy_url_encoded_name_pattern": self.LEGACY_URL_ENCODED_NAME_PATTERN,
            "blacklist_keywords": self._blacklist_sql_patterns(),
        }
        term_conditions = []
        term_scores = []
        haystack = "COALESCE(d.title, '') || ' ' || COALESCE(d.file_name, '') || ' ' || c.content"
        normalized_haystack = f"regexp_replace(({haystack}), '\\s+', '', 'g')"
        for idx, term in enumerate(terms[:20]):
            param = f"term_{idx}"
            norm_param = f"norm_term_{idx}"
            normalized_term = re.sub(r"\s+", "", term)
            params[param] = f"%{term}%"
            params[norm_param] = f"%{normalized_term}%"
            term_conditions.append(
                f"(({haystack}) ILIKE :{param} OR {normalized_haystack} ILIKE :{norm_param})"
            )
            content_match = (
                f"(c.content ILIKE :{param} OR "
                f"regexp_replace(c.content, '\\s+', '', 'g') ILIKE :{norm_param})"
            )
            section_match = f"COALESCE(c.section_path, '') ILIKE :{param}"
            title_match = (
                f"(COALESCE(d.title, '') ILIKE :{param} OR "
                f"COALESCE(d.file_name, '') ILIKE :{param})"
            )
            if term in project_terms:
                term_scores.append(
                    f"""
                    CASE
                      WHEN {title_match}
                      THEN 8.0
                      WHEN {content_match}
                      THEN 2.5
                      WHEN {section_match}
                      THEN 1.5
                      ELSE 0
                    END
                    """
                )
                continue
            term_scores.append(
                f"""
                CASE
                  WHEN {section_match}
                  THEN 3.0
                  WHEN {content_match}
                  THEN 2.2
                  WHEN {title_match}
                  THEN 0.3
                  ELSE 0
                END
                """
            )
        lexical_condition = " OR ".join(term_conditions) or "false"
        lexical_score = " + ".join(term_scores) or "0"
        rows = await db.execute(
            text(
                f"""
                SELECT c.id AS chunk_id, c.document_id, d.title AS document_title,
                       d.file_name AS document_name,
                       c.content, c.page_start, c.page_end, c.section_path,
                       c.metadata AS metadata,
                       d.source_url, d.preview_url, d.download_url,
                       d.storage_bucket, d.storage_object_key,
                       COALESCE(d.source_url, d.preview_url, d.download_url) AS url,
                       (similarity(c.content, :query) + ({lexical_score})::float) AS score
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.is_active = true
                  AND d.deleted_at IS NULL
                  AND d.file_name !~* :legacy_url_encoded_name_pattern
                  AND NOT ({self._document_blacklist_sql()})
                  AND (:document_ids_is_null OR d.id = ANY(CAST(:document_ids AS uuid[])))
                  AND (({lexical_condition}) OR similarity(c.content, :query) > 0.05)
                ORDER BY score DESC
                LIMIT :top_k
                """
            ),
            params,
        )
        return [self._normalize_result({**dict(row._mapping), "source": "keyword"}) for row in rows]

    async def _qa_search(
        self, db: AsyncSession, query: str, top_k: int, document_ids: list[str] | None = None
    ) -> list[dict]:
        # 向量召回
        try:
            embedding = (await self.model_service.embed([query]))[0]
            vector_literal = "[" + ",".join(str(x) for x in embedding) + "]"
            vector_rows = await db.execute(
                text(
                    f"""
                    SELECT q.id AS qa_pair_id, q.question AS qa_question, q.answer AS qa_answer,
                           q.source_document_id AS document_id,
                           d.title AS document_title, d.file_name AS document_name,
                           q.question || E'\n' || q.answer AS content,
                           NULL::integer AS page_start, NULL::integer AS page_end,
                           'QA问答对' AS section_path,
                           q.source_url AS qa_source_url,
                           d.source_url, d.preview_url, d.download_url,
                           d.storage_bucket, d.storage_object_key,
                           q.tags,
                           COALESCE(q.source_url, d.source_url, d.preview_url, d.download_url) AS url,
                           1 - (qe.embedding <=> CAST(:embedding AS vector)) AS score
                    FROM qa_pair_embeddings qe
                    JOIN qa_pairs q ON q.id = qe.qa_pair_id
                    LEFT JOIN documents d ON d.id = q.source_document_id
                    WHERE q.status = 'enabled'
                      AND q.deleted_at IS NULL
                      AND (
                        q.source_document_id IS NULL
                        OR (
                          d.deleted_at IS NULL
                          AND d.file_name !~* :legacy_url_encoded_name_pattern
                          AND NOT ({self._document_blacklist_sql()})
                        )
                      )
                      AND (:document_ids_is_null OR q.source_document_id = ANY(CAST(:document_ids AS uuid[])))
                    ORDER BY qe.embedding <=> CAST(:embedding AS vector)
                    LIMIT :top_k
                    """
                ),
                {
                    "embedding": vector_literal,
                    "top_k": top_k,
                    "document_ids": document_ids,
                    "document_ids_is_null": document_ids is None,
                    "legacy_url_encoded_name_pattern": self.LEGACY_URL_ENCODED_NAME_PATTERN,
                    "blacklist_keywords": self._blacklist_sql_patterns(),
                },
            )
            vector_results = [self._normalize_result({**dict(row._mapping), "source": "qa_vector"}) for row in vector_rows]
        except Exception:
            vector_results = []

        # 文本召回（关键词+相似度）
        text_rows = await db.execute(
            text(
                f"""
                SELECT q.id AS qa_pair_id, q.question AS qa_question, q.answer AS qa_answer,
                       q.source_document_id AS document_id,
                       d.title AS document_title, d.file_name AS document_name,
                       q.question || E'\n' || q.answer AS content,
                       NULL::integer AS page_start, NULL::integer AS page_end,
                       'QA问答对' AS section_path,
                       q.source_url AS qa_source_url,
                       d.source_url, d.preview_url, d.download_url,
                       d.storage_bucket, d.storage_object_key,
                       q.tags,
                       COALESCE(q.source_url, d.source_url, d.preview_url, d.download_url) AS url,
                       similarity(q.question, :query) AS score
                FROM qa_pairs q
                LEFT JOIN documents d ON d.id = q.source_document_id
                WHERE q.status = 'enabled'
                  AND q.deleted_at IS NULL
                  AND (
                    q.source_document_id IS NULL
                    OR (
                      d.deleted_at IS NULL
                      AND d.file_name !~* :legacy_url_encoded_name_pattern
                      AND NOT ({self._document_blacklist_sql()})
                    )
                  )
                  AND (:document_ids_is_null OR q.source_document_id = ANY(CAST(:document_ids AS uuid[])))
                  AND (q.question ILIKE :keyword OR similarity(q.question, :query) > 0.05)
                ORDER BY score DESC
                LIMIT :top_k
                """
            ),
            {
                "query": query,
                "keyword": f"%{query}%",
                "top_k": top_k,
                "document_ids": document_ids,
                "document_ids_is_null": document_ids is None,
                "legacy_url_encoded_name_pattern": self.LEGACY_URL_ENCODED_NAME_PATTERN,
                "blacklist_keywords": self._blacklist_sql_patterns(),
            },
        )
        text_results = [self._normalize_result({**dict(row._mapping), "source": "qa_text"}) for row in text_rows]

        # 向量 + 文本倒数排名融合
        return self._rrf([vector_results, text_results])

    def _rrf(self, result_sets: list[list[dict]]) -> list[dict]:
        merged: dict[str, dict] = {}
        k = 60
        for results in result_sets:
            for rank, item in enumerate(results, start=1):
                key = str(item.get("chunk_id") or item.get("qa_pair_id"))
                if key not in merged:
                    merged[key] = {**item, "rrf_score": 0.0, "sources": []}
                merged[key]["rrf_score"] += 1 / (k + rank)
                merged[key]["sources"].append(item.get("source"))
        return sorted(merged.values(), key=lambda x: x["rrf_score"], reverse=True)

    async def _rerank(self, query: str, candidates: list[dict]) -> list[dict]:
        if not self.rag_settings.get("rerank_enabled", self.settings.rerank_enabled):
            return self._fallback_rerank(candidates)
        return await self.rerank_service.rerank(query, candidates)

    async def _expand_adjacent_context(
        self,
        db: AsyncSession,
        query: str,
        final: list[dict],
    ) -> list[dict]:
        if db is None or not final:
            return final

        anchor_ids = [
            str(item["chunk_id"])
            for item in final
            if item.get("chunk_id") and self._should_expand_adjacent_context(query, item)
        ]
        if not anchor_ids:
            return final

        rows = await db.execute(
            text(
                f"""
                WITH anchors AS (
                  SELECT id, document_id, chunk_no
                  FROM document_chunks
                  WHERE id = ANY(CAST(:chunk_ids AS uuid[]))
                    AND is_active = true
                )
                SELECT a.id AS anchor_id,
                       a.chunk_no AS anchor_chunk_no,
                       c.id AS chunk_id, c.document_id, d.title AS document_title,
                       d.file_name AS document_name,
                       c.content, c.page_start, c.page_end, c.section_path,
                       c.chunk_no, c.chunk_type, c.metadata AS metadata,
                       d.source_url, d.preview_url, d.download_url,
                       d.storage_bucket, d.storage_object_key,
                       COALESCE(d.source_url, d.preview_url, d.download_url) AS url
                FROM anchors a
                JOIN document_chunks c
                  ON c.document_id = a.document_id
                 AND c.chunk_no IN (a.chunk_no - 1, a.chunk_no + 1)
                JOIN documents d ON d.id = c.document_id
                WHERE c.is_active = true
                  AND c.chunk_type != 'parent'
                  AND d.deleted_at IS NULL
                  AND d.file_name !~* :legacy_url_encoded_name_pattern
                  AND NOT ({self._document_blacklist_sql()})
                ORDER BY a.chunk_no, c.chunk_no
                """
            ),
            {
                "chunk_ids": anchor_ids,
                "legacy_url_encoded_name_pattern": self.LEGACY_URL_ENCODED_NAME_PATTERN,
                "blacklist_keywords": self._blacklist_sql_patterns(),
            },
        )
        neighbors_by_anchor: dict[str, list[dict]] = {}
        for row in rows:
            data = dict(row._mapping)
            anchor_id = str(data.pop("anchor_id"))
            neighbor = self._normalize_result(
                {
                    **data,
                    "source": "adjacent_context",
                    "sources": ["adjacent_context"],
                    "score": 0,
                }
            )
            neighbors_by_anchor.setdefault(anchor_id, []).append(neighbor)

        if not neighbors_by_anchor:
            return final

        expanded: list[dict] = []
        seen: set[str] = set()

        def append_item(item: dict) -> None:
            key = str(item.get("chunk_id") or item.get("qa_pair_id") or id(item))
            if key in seen:
                return
            seen.add(key)
            expanded.append(item)

        for item in final:
            chunk_id = str(item.get("chunk_id") or "")
            neighbors = neighbors_by_anchor.get(chunk_id, [])
            anchor_no = self._as_int(
                next((neighbor.get("anchor_chunk_no") for neighbor in neighbors), None)
            )
            for neighbor in neighbors:
                if anchor_no is not None and self._as_int(neighbor.get("chunk_no")) is not None:
                    if int(neighbor["chunk_no"]) < anchor_no:
                        append_item(neighbor)
            append_item(item)
            for neighbor in neighbors:
                if anchor_no is None or self._as_int(neighbor.get("chunk_no")) is None:
                    append_item(neighbor)
                elif int(neighbor["chunk_no"]) > anchor_no:
                    append_item(neighbor)
        return expanded

    def _should_expand_adjacent_context(self, query: str, item: dict) -> bool:
        content = str(item.get("content") or "").strip()
        if not content:
            return False
        normalized_query = self._normalize_query_text(query)
        compact_content = re.sub(r"\s+", "", content)
        if "报名表" in compact_content and not any(
            marker in compact_content for marker in ("参赛要求", "活动时间", "活动地点", "活动流程", "比赛细则")
        ):
            return False
        if re.search(r"(参赛要求|活动流程|比赛细则|报名办法|报名要求|活动时间|活动地点|奖项设置|要求|规则|条件|流程|如下)[:：]\s*$", content[-160:]):
            return True
        if re.match(r"^\s*[（(]?\d+[）)]", content) and any(
            marker in normalized_query for marker in ("要求", "规则", "条件", "流程", "怎么", "什么")
        ):
            return True
        detail_intent = any(
            marker in normalized_query
            for marker in ("要求", "规则", "条件", "流程", "步骤", "报名", "资格", "时间", "什么时候", "什么时间", "开始", "有哪些", "是什么")
        )
        if not detail_intent:
            return False
        evidence_markers = ("参赛要求", "活动时间", "活动地点", "比赛项目", "活动流程", "比赛细则", "奖项设置")
        if any(marker in compact_content for marker in evidence_markers):
            return True
        terms = [re.sub(r"\s+", "", term) for term in self._query_terms(query) if len(term) >= 2]
        return any(term and term in compact_content for term in terms)

    def _as_int(self, value) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _rerank_candidate_count(self, top_k: int, available: int) -> int:
        configured = max(top_k, int(self.rag_settings["rerank_max_candidates"]))
        return min(available, configured)

    def _limit(self, value, fallback: int, max_value: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = fallback
        return max(1, min(parsed, max_value))

    def _fallback_rerank(self, candidates: list[dict]) -> list[dict]:
        for idx, item in enumerate(candidates, start=1):
            item["rerank_score"] = float(item.get("rrf_score", 0)) + max(0, 1 / (idx + 1))
        return sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)

    def _normalize_context_constraints(self, constraints: dict | None) -> dict:
        if not isinstance(constraints, dict):
            return {}

        def clean_text(value: object, limit: int = 320) -> str:
            return self._clip_business_text(str(value or "").strip(), limit)

        target_documents = constraints.get("target_documents")
        if not isinstance(target_documents, list):
            target_documents = []
        normalized_targets = [
            clean_text(item, 220)
            for item in target_documents
            if clean_text(item, 220)
        ][:5]

        constraint_terms = constraints.get("constraint_terms")
        if not isinstance(constraint_terms, list):
            constraint_terms = []
        normalized_terms = []
        for item in constraint_terms:
            text = re.sub(r"\s+", "", clean_text(item, 220))
            if text and text not in normalized_terms:
                normalized_terms.append(text)
        for item in (
            constraints.get("active_topic"),
            constraints.get("user_goal"),
            constraints.get("resume_query"),
            *normalized_targets,
        ):
            text = re.sub(r"\s+", "", clean_text(item, 220))
            if text and text not in normalized_terms:
                normalized_terms.append(text)

        strength = str(constraints.get("constraint_strength") or "none").strip()
        if strength not in {"none", "soft", "strict"}:
            strength = "none"
        is_followup = bool(constraints.get("is_followup"))
        if is_followup and strength == "none":
            strength = "soft"

        return {
            "original_query": clean_text(constraints.get("original_query")),
            "resolved_query": clean_text(constraints.get("resolved_query")),
            "retrieval_query": clean_text(constraints.get("retrieval_query"), 1200),
            "intent": clean_text(constraints.get("intent"), 80) or "unknown",
            "is_followup": is_followup,
            "uses_history": bool(constraints.get("uses_history")),
            "uses_context_state": bool(constraints.get("uses_context_state")),
            "active_topic": clean_text(constraints.get("active_topic"), 220),
            "user_goal": clean_text(constraints.get("user_goal"), 320),
            "resume_query": clean_text(constraints.get("resume_query"), 320),
            "target_documents": normalized_targets,
            "constraint_terms": normalized_terms,
            "constraint_strength": strength,
        }

    def _classify_query_business_domain(self, query: str, constraints: dict | None = None) -> dict:
        constraints = constraints or {}
        parts = [query]
        if constraints.get("is_followup"):
            parts.extend(
                str(constraints.get(key) or "")
                for key in ("active_topic", "user_goal", "resume_query")
            )
            parts.extend(str(item) for item in constraints.get("target_documents") or [])
        combined = " ".join(part for part in parts if str(part or "").strip())
        classified = self._classify_business_domain(combined)
        if constraints.get("is_followup") and classified.get("domain") != "general":
            classified = {
                **classified,
                "source": "query_with_context",
                "context_enforced": True,
            }
        return classified

    def _apply_context_constraints(
        self,
        constraints: dict,
        candidates: list[dict],
        stage: str,
    ) -> tuple[list[dict], dict]:
        if not candidates:
            return candidates, {
                "stage": stage,
                "enabled": False,
                "kept": 0,
                "removed": 0,
                "fallback": False,
            }
        if not constraints or constraints.get("constraint_strength") == "none":
            return candidates, {
                "stage": stage,
                "enabled": False,
                "kept": len(candidates),
                "removed": 0,
                "fallback": False,
            }

        target_documents = constraints.get("target_documents") or []
        if not target_documents:
            return candidates, {
                "stage": stage,
                "enabled": True,
                "kept": len(candidates),
                "removed": 0,
                "fallback": False,
                "reason": "no_target_documents",
                "context": self._context_constraint_summary(constraints),
            }

        kept: list[dict] = []
        removed: list[dict] = []
        for item in candidates:
            if self._matches_target_documents(item, target_documents):
                kept.append(self._annotate_context_constraint(item, constraints, matched=True))
            else:
                removed.append(self._annotate_context_constraint(item, constraints, matched=False))

        fallback = False
        if not kept:
            fallback = True
            kept = [self._annotate_context_constraint(item, constraints, matched=False) for item in candidates]
        elif constraints.get("constraint_strength") == "soft" and stage in {"recall", "rerank"}:
            supplemental = sorted(removed, key=self._threshold_score, reverse=True)[: max(0, 3 - len(kept))]
            kept.extend(supplemental)

        return kept, {
            "stage": stage,
            "enabled": True,
            "kept": len(kept),
            "removed": 0 if fallback else max(0, len(candidates) - len(kept)),
            "fallback": fallback,
            "context": self._context_constraint_summary(constraints),
            "removed_documents": self._business_filter_removed_documents(removed, limit=8),
        }

    def _annotate_context_constraint(self, item: dict, constraints: dict, matched: bool) -> dict:
        return {
            **item,
            "context_constraint_matched": matched,
            "context_constraint_strength": constraints.get("constraint_strength"),
        }

    def _matches_target_documents(self, item: dict, target_documents: list[str]) -> bool:
        haystack = self._normalize_query_text(
            " ".join(
                [
                    str(item.get("document_title") or ""),
                    str(item.get("document_name") or ""),
                    str(item.get("file_name") or ""),
                ]
            )
        )
        if not haystack:
            return False
        for target in target_documents:
            normalized = self._normalize_query_text(str(target or ""))
            if not normalized:
                continue
            if normalized in haystack or haystack in normalized:
                return True
            target_terms = [term for term in self._query_terms(str(target)) if len(term) >= 3]
            if target_terms and any(self._normalize_query_text(term) in haystack for term in target_terms):
                return True
        return False

    def _context_constraint_summary(self, constraints: dict) -> dict:
        return {
            "intent": constraints.get("intent"),
            "is_followup": constraints.get("is_followup"),
            "constraint_strength": constraints.get("constraint_strength"),
            "active_topic": constraints.get("active_topic"),
            "target_documents": constraints.get("target_documents") or [],
        }

    def _merge_context_constraint_stats(self, *stats: dict) -> dict:
        return {
            "enabled": any(stat.get("enabled") for stat in stats if stat),
            "stages": [stat for stat in stats if stat],
            "removed_total": sum(int(stat.get("removed") or 0) for stat in stats if stat),
            "fallback_used": any(stat.get("fallback") for stat in stats if stat),
        }

    def _filter_by_business_domain(
        self,
        query_domain: dict,
        candidates: list[dict],
        stage: str,
    ) -> tuple[list[dict], dict]:
        if not candidates:
            return candidates, {
                "stage": stage,
                "enabled": False,
                "kept": 0,
                "removed": 0,
                "fallback": False,
            }
        domain = str(query_domain.get("domain") or "general")
        confidence = float(query_domain.get("confidence") or 0)
        if domain == "general" or confidence < 0.62:
            return candidates, {
                "stage": stage,
                "enabled": False,
                "query_domain": query_domain,
                "kept": len(candidates),
                "removed": 0,
                "fallback": False,
            }

        annotated = [self._annotate_business_domain(item) for item in candidates]
        kept: list[dict] = []
        removed: list[dict] = []
        for item in annotated:
            item_domain = str(item.get("business_domain") or "general")
            item_confidence = float(item.get("business_domain_confidence") or 0)
            if self._business_domain_matches(domain, item_domain, item_confidence):
                kept.append(item)
            else:
                removed.append(item)

        fallback = False
        if not kept:
            fallback = True
            kept = sorted(
                annotated,
                key=lambda item: (
                    self._business_domain_fallback_score(query_domain, item),
                    self._threshold_score(item),
                ),
                reverse=True,
            )[: max(1, min(len(annotated), 3))]
        elif stage in {"recall", "rerank"} and len(kept) < min(3, len(annotated)):
            # 重排前保留少量低置信度候选，避免名称很窄的文档完全失去机会。
            supplemental = [
                item
                for item in removed
                if str(item.get("business_domain") or "general") == "general"
                and float(item.get("business_domain_confidence") or 0) < 0.72
            ]
            supplemental = sorted(supplemental, key=self._threshold_score, reverse=True)[: max(0, 3 - len(kept))]
            kept.extend(supplemental)

        return kept, {
            "stage": stage,
            "enabled": True,
            "query_domain": query_domain,
            "kept": len(kept),
            "removed": max(0, len(annotated) - len(kept)),
            "fallback": fallback,
            "removed_documents": self._business_filter_removed_documents(removed, limit=8),
        }

    def _business_domain_matches(self, query_domain: str, item_domain: str, item_confidence: float) -> bool:
        if item_domain == query_domain:
            return True
        if item_domain == "general" and item_confidence < 0.74:
            return True
        return False

    def _business_domain_fallback_score(self, query_domain: dict, item: dict) -> float:
        domain = str(query_domain.get("domain") or "general")
        item_domain = str(item.get("business_domain") or "general")
        if item_domain == domain:
            return 2.0
        if item_domain == "general":
            return 1.0
        return -1.0 * float(item.get("business_domain_confidence") or 0)

    def _business_filter_removed_documents(self, removed: list[dict], limit: int = 8) -> list[dict]:
        seen: dict[str, dict] = {}
        for item in removed:
            doc_id = str(item.get("document_id") or item.get("qa_pair_id") or "")
            if not doc_id or doc_id in seen:
                continue
            seen[doc_id] = {
                "document_id": doc_id,
                "document_title": self._display_document_title(item),
                "business_domain": item.get("business_domain"),
                "business_domain_confidence": item.get("business_domain_confidence"),
                "business_domain_hits": item.get("business_domain_hits") or [],
            }
            if len(seen) >= limit:
                break
        return list(seen.values())

    def _merge_business_filter_stats(self, *stats: dict) -> dict:
        merged = {
            "enabled": any(stat.get("enabled") for stat in stats),
            "stages": [stat for stat in stats if stat],
            "removed_total": sum(int(stat.get("removed") or 0) for stat in stats if stat),
            "fallback_used": any(stat.get("fallback") for stat in stats if stat),
        }
        for stat in stats:
            if stat.get("query_domain"):
                merged["query_domain"] = stat["query_domain"]
                break
        return merged

    def _annotate_business_domain(self, item: dict) -> dict:
        classified = self._classify_business_domain(
            " ".join(
                [
                    str(item.get("document_title") or ""),
                    str(item.get("document_name") or ""),
                    str(item.get("section_path") or ""),
                    self._clip_business_text(str(item.get("content") or "")),
                    " ".join(str(tag) for tag in item.get("tags") or []),
                ]
            )
        )
        return {
            **item,
            "business_domain": classified["domain"],
            "business_domain_confidence": classified["confidence"],
            "business_domain_hits": classified["matched_terms"],
        }

    def _clip_business_text(self, text: str, limit: int = 420) -> str:
        text = text.strip()
        if len(text) <= limit:
            return text
        return text[:limit]

    def _classify_business_domain(self, text: str) -> dict:
        normalized = self._normalize_query_text(text)
        if not normalized:
            return {"domain": "general", "confidence": 0.0, "matched_terms": []}

        domain_terms: dict[str, tuple[str, ...]] = {
            "scholarship_aid": (
                "奖学金",
                "国家奖学金",
                "励志奖学金",
                "助学金",
                "资助",
                "困难认定",
                "家庭经济困难",
                "贫困生",
                "奖助",
                "助学贷款",
                "勤工助学",
                "申请材料",
                "评定",
            ),
            "travel_reimbursement": (
                "差旅",
                "出差",
                "差旅费",
                "差旅审批",
                "网上差旅",
                "报销",
                "借款",
                "审批单",
                "住宿费",
                "交通费",
                "公务出行",
            ),
            "teaching": (
                "课程",
                "学分",
                "考试",
                "补考",
                "重修",
                "选课",
                "培养方案",
                "成绩",
                "教务",
            ),
            "dormitory": (
                "宿舍",
                "寝室",
                "住宿",
                "公寓",
                "水电费",
                "退宿",
                "调宿",
            ),
            "student_affairs": (
                "转学",
                "休学",
                "复学",
                "退学",
                "学生证",
                "请假",
                "处分",
                "学籍",
            ),
        }
        negative_terms: dict[str, tuple[str, ...]] = {
            "scholarship_aid": ("差旅", "出差", "报销", "审批单", "住宿费", "交通费"),
            "travel_reimbursement": ("奖学金", "助学金", "资助", "困难认定", "家庭经济困难"),
        }

        scores: dict[str, float] = {}
        hits: dict[str, list[str]] = {}
        for domain, terms in domain_terms.items():
            domain_hits = [term for term in terms if term in normalized]
            if not domain_hits:
                continue
            score = 0.0
            for term in domain_hits:
                if len(term) >= 4:
                    score += 2.0
                else:
                    score += 1.0
            for term in negative_terms.get(domain, ()):
                if term in normalized:
                    score -= 2.5
            scores[domain] = score
            hits[domain] = domain_hits

        if not scores:
            return {"domain": "general", "confidence": 0.0, "matched_terms": []}

        ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
        domain, score = ranked[0]
        if score <= 0:
            return {"domain": "general", "confidence": 0.0, "matched_terms": []}
        runner_up = ranked[1][1] if len(ranked) > 1 else 0.0
        confidence = min(0.98, 0.52 + score * 0.11 + max(0.0, score - runner_up) * 0.05)
        if confidence < 0.58:
            return {"domain": "general", "confidence": round(confidence, 3), "matched_terms": hits.get(domain, [])}
        return {
            "domain": domain,
            "confidence": round(confidence, 3),
            "matched_terms": hits.get(domain, []),
        }

    def _apply_local_rank_adjustments(
        self,
        query: str,
        candidates: list[dict],
        query_domain: dict | None = None,
        context_constraints: dict | None = None,
    ) -> list[dict]:
        terms = self._query_terms(query)
        query_domain = query_domain or self._classify_business_domain(query)
        context_constraints = context_constraints or {}
        if not terms and context_constraints.get("constraint_strength") == "none":
            return candidates
        adjusted = []
        for item in candidates:
            haystack = re.sub(
                r"\s+",
                "",
                " ".join(
                    [
                        str(item.get("document_title") or ""),
                        str(item.get("document_name") or ""),
                        str(item.get("section_path") or ""),
                        str(item.get("content") or ""),
                    ]
                ),
            )
            title_haystack = re.sub(
                r"\s+",
                "",
                " ".join(
                    [
                        str(item.get("document_title") or ""),
                        str(item.get("document_name") or ""),
                    ]
                ),
            )
            evidence_haystack = re.sub(
                r"\s+",
                "",
                " ".join(
                    [
                        str(item.get("section_path") or ""),
                        str(item.get("content") or ""),
                    ]
                ),
            )
            lexical_hits = sum(1 for term in terms if re.sub(r"\s+", "", term) in haystack)
            title_hits = sum(1 for term in terms if re.sub(r"\s+", "", term) in title_haystack)
            evidence_hits = sum(1 for term in terms if re.sub(r"\s+", "", term) in evidence_haystack)
            intent_score = self._intent_alignment_score(
                self._normalize_query_text(query),
                evidence_haystack,
            )
            noise_penalty = self._noise_penalty(str(item.get("content") or ""))
            qa_mismatch_penalty = self._qa_mismatch_penalty(query, item, terms, evidence_haystack)
            annotated = self._annotate_business_domain(item)
            business_score = self._business_alignment_score(query_domain, annotated)
            context_score = self._context_alignment_score(context_constraints, annotated, haystack)
            base_score = float(
                item.get("rerank_score")
                or item.get("rrf_score")
                or item.get("score")
                or 0
            )
            lexical_score = lexical_hits * 0.5 + title_hits * 4.0 + evidence_hits * 1.7 + intent_score
            adjusted.append(
                {
                    **annotated,
                    "lexical_score": lexical_score,
                    "intent_score": intent_score,
                    "business_score": business_score,
                    "context_score": context_score,
                    "noise_penalty": noise_penalty,
                    "qa_mismatch_penalty": qa_mismatch_penalty,
                    "combined_score": base_score + lexical_score + business_score + context_score - noise_penalty - qa_mismatch_penalty,
                }
            )
        return sorted(adjusted, key=lambda x: x.get("combined_score", 0), reverse=True)

    def _context_alignment_score(self, constraints: dict, item: dict, haystack: str) -> float:
        if not constraints or constraints.get("constraint_strength") == "none":
            return 0.0
        score = 0.0
        if self._matches_target_documents(item, constraints.get("target_documents") or []):
            score += 5.0 if constraints.get("constraint_strength") == "strict" else 2.5
        for term in constraints.get("constraint_terms") or []:
            normalized = self._normalize_query_text(str(term))
            if len(normalized) >= 4 and normalized in haystack:
                score += 0.8
        return min(score, 8.0)

    def _business_alignment_score(self, query_domain: dict, item: dict) -> float:
        domain = str(query_domain.get("domain") or "general")
        confidence = float(query_domain.get("confidence") or 0)
        if domain == "general" or confidence < 0.62:
            return 0.0
        item_domain = str(item.get("business_domain") or "general")
        item_confidence = float(item.get("business_domain_confidence") or 0)
        if item_domain == domain:
            return 3.2 * confidence + min(1.8, item_confidence * 1.6)
        if item_domain == "general" and item_confidence < 0.74:
            return 0.0
        return -5.0 * confidence - item_confidence

    def _qa_mismatch_penalty(self, query: str, item: dict, terms: list[str], evidence: str) -> float:
        source = str(item.get("source") or "")
        if not source.startswith("qa"):
            return 0.0
        normalized_query = self._normalize_query_text(query)
        school_intent = any(
            marker in normalized_query
            for marker in ("比赛", "参赛", "体育文化节", "活动", "讲座", "测试", "报名")
        )
        if not school_intent:
            return 0.0
        meaningful_terms = [
            re.sub(r"\s+", "", term)
            for term in terms
            if len(term) >= 2 and term not in {"什么时候", "什么时间", "是什么", "有哪些", "开始", "要求"}
        ]
        if not meaningful_terms:
            return 0.0
        return 0.0 if any(term and term in evidence for term in meaningful_terms) else 5.0

    def _intent_alignment_score(self, normalized_query: str, evidence: str) -> float:
        if not normalized_query or not evidence:
            return 0.0
        score = 0.0
        payment_intent = any(term in normalized_query for term in ("付款", "支付", "货款"))
        payment_shape = any(term in normalized_query for term in ("比例", "节点", "方式", "款项"))
        if payment_intent and payment_shape:
            clause_signal = any(term in evidence for term in ("付款方式", "支付方式", "货款支付"))
            amount_signal = any(
                term in evidence
                for term in ("合同总价款", "合同总金额", "合同总额", "合同金额", "合同价款", "合同剩余款项")
            )
            percent_signal = bool(re.search(r"\d{1,3}\s*%|百分之", evidence))
            if clause_signal:
                score += 2.2
            if amount_signal:
                score += 2.0
            if percent_signal:
                score += 1.4
            if "发票" in evidence:
                score += 0.5
            product_payment_signal = any(
                term in evidence
                for term in ("支付管理", "在线支付", "支付平台", "支付渠道", "支付接口", "退款", "订单", "缴费")
            )
            if product_payment_signal and not (clause_signal or amount_signal or percent_signal):
                score -= 2.8
        return score

    def _noise_penalty(self, content: str) -> float:
        if not content:
            return 0.0
        datetime_hits = len(re.findall(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", content))
        short_datetime_hits = len(re.findall(r"\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?", content))
        repeated_name_hits = max(0, content.count("庄艳蓓") - 1)
        signal_terms = ["合同总价", "甲方", "乙方", "付款", "验收", "保密", "违约", "争议", "生效"]
        signal_hits = sum(1 for term in signal_terms if term in content)
        penalty = datetime_hits * 0.08 + short_datetime_hits * 0.05 + repeated_name_hits * 0.08
        if signal_hits:
            penalty *= 0.35
        return min(1.2, penalty)

    def _apply_threshold_filter(self, candidates: list[dict]) -> list[dict]:
        rerank_threshold = float(self.rag_settings["rerank_threshold"])
        similarity_threshold = float(self.rag_settings["similarity_threshold"])
        if not candidates:
            return candidates
        filtered: list[dict] = []
        for item in candidates:
            if self._threshold_score(item) >= rerank_threshold:
                filtered.append(item)
        if not filtered:
            fallback = [
                item for item in candidates
                if self._threshold_score(item) >= similarity_threshold
            ]
            filtered = fallback or candidates[:1]
        return filtered

    def _policy_coverage_plan(self, query: str, contexts: list[dict]) -> dict:
        expected_facets = self._expected_policy_facets(query)
        if not expected_facets:
            return {
                "enabled": False,
                "question_type": "general",
                "expected_facets": [],
                "covered_facets": [],
                "missing_facets": [],
                "supplemented_facets": [],
            }
        covered = self._covered_policy_facets(contexts, expected_facets)
        missing = [facet for facet in expected_facets if facet not in covered]
        return {
            "enabled": True,
            "question_type": "policy_process",
            "expected_facets": expected_facets,
            "covered_facets": covered,
            "missing_facets": missing,
            "supplemented_facets": [],
        }

    async def _complete_policy_context(
        self,
        db: AsyncSession,
        query: str,
        contexts: list[dict],
        query_domain: dict,
        coverage: dict,
    ) -> tuple[list[dict], dict]:
        if db is None or not contexts or not coverage.get("missing_facets"):
            return contexts, coverage

        expanded = list(contexts)
        seen = {self._result_key(item) for item in expanded}
        anchor_document_ids = self._policy_anchor_document_ids(contexts)
        supplemented: list[str] = []
        for facet in coverage["missing_facets"]:
            supplement_query = self._policy_facet_query(query, facet)
            supplemental = await self._policy_keyword_supplement_search(
                db,
                supplement_query,
                facet,
                anchor_document_ids,
                query_domain,
            )
            for item in supplemental:
                key = self._result_key(item)
                if key in seen:
                    continue
                expanded.append(item)
                seen.add(key)
                if facet not in supplemented:
                    supplemented.append(facet)
                if len(expanded) >= 12:
                    break

        covered = self._covered_policy_facets(expanded, coverage["expected_facets"])
        return expanded, {
            **coverage,
            "covered_facets": covered,
            "missing_facets": [facet for facet in coverage["expected_facets"] if facet not in covered],
            "supplemented_facets": supplemented,
            "anchor_document_ids": anchor_document_ids,
        }

    async def _policy_keyword_supplement_search(
        self,
        db: AsyncSession,
        supplement_query: str,
        facet: str,
        anchor_document_ids: list[str],
        query_domain: dict,
    ) -> list[dict]:
        document_ids = anchor_document_ids or None
        results = await self._keyword_search(db, supplement_query, top_k=8, document_ids=document_ids)
        if not results and anchor_document_ids:
            results = await self._keyword_search(db, supplement_query, top_k=8, document_ids=None)
        results, _ = self._filter_by_business_domain(query_domain, results, stage=f"policy_{facet}")
        return [
            {
                **item,
                "source": "policy_supplement",
                "policy_facet": facet,
            }
            for item in results
            if self._item_covers_policy_facet(item, facet)
        ][:3]

    def _expected_policy_facets(self, query: str) -> list[str]:
        normalized = self._normalize_query_text(query)
        policy_markers = (
            "政策",
            "制度",
            "规定",
            "办法",
            "流程",
            "办理",
            "申请",
            "需要准备",
            "材料",
            "条件",
            "资格",
            "要求",
            "手续",
            "怎么",
            "如何",
        )
        domain_markers = (
            "转学",
            "休学",
            "复学",
            "退学",
            "奖学金",
            "助学金",
            "差旅",
            "报销",
            "宿舍",
            "调宿",
        )
        if not any(marker in normalized for marker in policy_markers):
            return []
        if not any(marker in normalized for marker in domain_markers):
            return []

        facets = ["conditions", "materials", "process"]
        if any(marker in normalized for marker in ("转学", "休学", "复学", "退学", "申请", "办理", "条件", "资格")):
            facets.extend(["restrictions", "special_cases", "post_requirements"])
        if any(marker in normalized for marker in ("跨省", "跨校", "户口", "迁移", "转学")):
            facets.append("cross_department")
        if any(marker in normalized for marker in ("时间", "多久", "几天", "几个月", "截止", "公示", "备案", "转学")):
            facets.append("timeline")
        return self._dedupe_terms(facets)

    def _policy_facet_terms(self) -> dict[str, tuple[str, ...]]:
        return {
            "conditions": ("条件", "资格", "符合", "申请", "应当", "可以", "转学理由", "患病", "特殊困难"),
            "materials": ("材料", "申请表", "证明", "成绩", "意见", "审批表", "备案表", "提交", "准备"),
            "process": ("流程", "程序", "办理", "审批", "审核", "确认", "转入", "转出", "报送"),
            "restrictions": ("不得", "不予", "不能", "禁止", "限制", "情形", "低学历层次", "定向就业", "未满一学期", "毕业前一年"),
            "special_cases": ("特殊", "非个人原因", "培养条件", "改变", "学校证明", "协调", "安排"),
            "post_requirements": ("公示", "备案", "完成后", "3个月", "三个月", "省级教育行政部门", "及时公示"),
            "cross_department": ("跨省", "户口", "迁移", "公安", "抄送", "所在地", "教育行政部门"),
            "timeline": ("时间", "期限", "3个月", "三个月", "公示", "完成后", "毕业前一年", "未满一学期"),
        }

    def _covered_policy_facets(self, contexts: list[dict], expected_facets: list[str]) -> list[str]:
        covered = []
        for facet in expected_facets:
            if any(self._item_covers_policy_facet(item, facet) for item in contexts):
                covered.append(facet)
        return covered

    def _item_covers_policy_facet(self, item: dict, facet: str) -> bool:
        terms = self._policy_facet_terms().get(facet, ())
        evidence = self._item_evidence(item)
        return any(self._normalize_query_text(term) in evidence for term in terms)

    def _policy_facet_query(self, query: str, facet: str) -> str:
        terms = " ".join(self._policy_facet_terms().get(facet, ())[:8])
        return f"{query} {terms}".strip()

    def _policy_anchor_document_ids(self, contexts: list[dict]) -> list[str]:
        doc_scores: dict[str, float] = {}
        for item in contexts:
            doc_id = str(item.get("document_id") or "")
            if not doc_id:
                continue
            doc_scores[doc_id] = max(doc_scores.get(doc_id, 0.0), self._threshold_score(item))
        return sorted(doc_scores, key=lambda doc_id: doc_scores[doc_id], reverse=True)[:2]

    def _result_key(self, item: dict) -> str:
        return str(item.get("chunk_id") or item.get("qa_pair_id") or f"{item.get('document_id')}:{item.get('content')}")

    def select_answer_context(self, query: str, results: list[dict]) -> list[dict]:
        if not results:
            return []

        policy_plan = self._policy_coverage_plan(query, results)
        max_chunks = 8 if policy_plan.get("enabled") else self.MAX_ANSWER_CONTEXT_CHUNKS
        max_docs = 2 if policy_plan.get("enabled") else self.MAX_ANSWER_CONTEXT_DOCS
        scored = [
            (index, self._with_answer_context_score(query, item))
            for index, item in enumerate(results)
            if item.get("document_id")
        ]
        if not scored:
            return []

        ranked = sorted(scored, key=lambda pair: pair[1].get("answer_context_score", 0), reverse=True)
        best_score = float(ranked[0][1].get("answer_context_score") or 0)
        selected_indexes: set[int] = set()
        selected_docs: list[str] = []
        per_doc_count: dict[str, int] = {}
        per_doc_limit = 6 if policy_plan.get("enabled") else 2

        def doc_selected(doc_id: str) -> bool:
            return doc_id in selected_docs

        def close_enough(score: float, term_hits: int) -> bool:
            if score >= best_score:
                return True
            if best_score <= 1.5:
                return score >= max(0.35, best_score * 0.82)
            if term_hits:
                return score >= best_score - max(2.2, best_score * 0.32)
            return score >= best_score - max(1.2, best_score * 0.18)

        for index, item in ranked:
            if len(selected_indexes) >= max_chunks:
                break
            doc_id = str(item.get("document_id") or "")
            if not doc_id:
                continue
            score = float(item.get("answer_context_score") or 0)
            term_hits = int(item.get("answer_term_hits") or 0)
            if selected_indexes and not doc_selected(doc_id):
                if len(selected_docs) >= max_docs or not close_enough(score, term_hits):
                    continue
                if self._is_low_signal_context(item) and term_hits == 0:
                    continue
            if per_doc_count.get(doc_id, 0) >= per_doc_limit:
                continue
            selected_indexes.add(index)
            per_doc_count[doc_id] = per_doc_count.get(doc_id, 0) + 1
            if doc_id not in selected_docs:
                selected_docs.append(doc_id)

        if not selected_indexes:
            selected_indexes.add(ranked[0][0])

        # 只为通过高置信度过滤的文档保留相邻扩展分块。
        selected_doc_set = {str(results[index].get("document_id")) for index in selected_indexes}
        for index, item in scored:
            if len(selected_indexes) >= max_chunks:
                break
            doc_id = str(item.get("document_id") or "")
            if doc_id not in selected_doc_set or doc_id not in per_doc_count:
                continue
            if index in selected_indexes or per_doc_count[doc_id] >= per_doc_limit:
                continue
            if item.get("source") == "adjacent_context" or int(item.get("answer_term_hits") or 0) > 0:
                selected_indexes.add(index)
                per_doc_count[doc_id] += 1

        if policy_plan.get("enabled"):
            covered = self._covered_policy_facets([results[index] for index in selected_indexes], policy_plan["expected_facets"])
            for facet in policy_plan["expected_facets"]:
                if facet in covered:
                    continue
                for index, item in scored:
                    if len(selected_indexes) >= max_chunks:
                        break
                    if index in selected_indexes:
                        continue
                    doc_id = str(item.get("document_id") or "")
                    if doc_id in selected_doc_set and self._item_covers_policy_facet(item, facet):
                        selected_indexes.add(index)
                        per_doc_count[doc_id] = per_doc_count.get(doc_id, 0) + 1
                        covered.append(facet)
                        break

        return [
            self._with_answer_context_score(query, item)
            for index, item in enumerate(results)
            if index in selected_indexes
        ]

    def citations_for_answer(self, query: str, answer: str, contexts: list[dict]) -> list[dict]:
        if not contexts or self._answer_declines_evidence(answer):
            return []

        doc_scores: dict[str, float] = {}
        for item in contexts:
            doc_id = str(item.get("document_id") or "")
            if not doc_id:
                continue
            evidence_score = self._answer_evidence_score(query, answer, item)
            usage_score = self._answer_usage_score(answer, item)
            rank_score = float(item.get("answer_context_score") or self._answer_context_score(query, item))
            doc_scores[doc_id] = max(doc_scores.get(doc_id, 0.0), usage_score * 10 + evidence_score + rank_score)

        ranked_docs = sorted(doc_scores, key=lambda doc_id: doc_scores[doc_id], reverse=True)
        used_docs = [
            doc_id
            for doc_id in ranked_docs
            if any(
                self._answer_usage_score(answer, item) > 0
                for item in contexts
                if str(item.get("document_id") or "") == doc_id
            )
        ]
        if not used_docs and ranked_docs:
            used_docs = ranked_docs[:1]
        used_doc_set = set(used_docs[: self.MAX_CITATION_DOCS])
        candidates = [
            item
            for item in contexts
            if str(item.get("document_id") or "") in used_doc_set
        ]
        scored = sorted(
            candidates,
            key=lambda item: (
                self._answer_usage_score(answer, item) * 10
                + self._answer_evidence_score(query, answer, item)
                + float(item.get("answer_context_score") or self._answer_context_score(query, item))
            ),
            reverse=True,
        )
        return self._citations(scored, query=query, answer=answer)

    def _with_answer_context_score(self, query: str, item: dict) -> dict:
        return {
            **item,
            "answer_context_score": round(self._answer_context_score(query, item), 4),
            "answer_term_hits": self._term_hit_count(self._meaningful_query_terms(query), self._item_evidence(item)),
        }

    def _answer_context_score(self, query: str, item: dict) -> float:
        terms = self._meaningful_query_terms(query)
        evidence = self._item_evidence(item)
        term_hits = self._term_hit_count(terms, evidence)
        title_hits = self._term_hit_count(terms, self._item_title_evidence(item))
        return (
            self._threshold_score(item)
            + term_hits * 0.7
            + title_hits * 1.2
            + max(0.0, float(item.get("intent_score") or 0)) * 0.4
            - self._noise_penalty(str(item.get("content") or "")) * 0.4
        )

    def _answer_evidence_score(self, query: str, answer: str, item: dict) -> float:
        evidence = self._item_evidence(item)
        answer_text = self._normalize_query_text(answer)
        if not evidence or not answer_text:
            return 0.0
        query_terms = self._meaningful_query_terms(query)
        query_hits = sum(1 for term in query_terms if term in evidence)
        answer_terms = self._answer_terms(answer_text)
        answer_hits = sum(1 for term in answer_terms if term in evidence)
        number_hits = sum(1 for term in self._number_terms(answer) if term in evidence)
        return query_hits * 1.2 + answer_hits * 0.6 + number_hits * 1.5

    def _answer_usage_score(self, answer: str, item: dict) -> float:
        evidence = self._item_evidence(item)
        answer_text = self._normalize_query_text(answer)
        if not evidence or not answer_text:
            return 0.0
        answer_hits = sum(1 for term in self._answer_terms(answer_text) if term in evidence)
        number_hits = sum(1 for term in self._number_terms(answer) if term in evidence)
        return answer_hits * 0.6 + number_hits * 1.5

    def _answer_terms(self, normalized_answer: str) -> list[str]:
        generic = {
            "根据资料",
            "相关资料",
            "可以",
            "需要",
            "没有",
            "明确",
            "显示",
            "说明",
            "这个",
            "问题",
            "回答",
        }
        terms: list[str] = []
        for match in re.findall(r"[\u4e00-\u9fffA-Za-z]{2,12}", normalized_answer):
            if match not in generic:
                terms.append(match)
        return self._dedupe_terms(terms[:30])

    def _number_terms(self, text: str) -> list[str]:
        return self._dedupe_terms(re.findall(r"\d+(?:\.\d+)?%?|\d{4}年|\d{1,2}月\d{1,2}日", text))

    def _meaningful_query_terms(self, query: str) -> list[str]:
        generic = {
            "请问",
            "什么",
            "是什么",
            "有哪些",
            "怎么",
            "如何",
            "这个",
            "那个",
            "之前",
            "刚才",
            "问题",
            "资料",
        }
        terms = []
        for term in self._query_terms(query):
            normalized = self._normalize_query_text(term)
            if len(normalized) < 2 or normalized in generic:
                continue
            terms.append(normalized)
        return self._dedupe_terms(terms)

    def _term_hit_count(self, terms: list[str], text: str) -> int:
        return sum(1 for term in terms if term and term in text)

    def _item_evidence(self, item: dict) -> str:
        return self._normalize_query_text(
            " ".join(
                [
                    str(item.get("document_title") or ""),
                    str(item.get("document_name") or ""),
                    str(item.get("section_path") or ""),
                    str(item.get("content") or ""),
                ]
            )
        )

    def _item_title_evidence(self, item: dict) -> str:
        return self._normalize_query_text(
            " ".join([str(item.get("document_title") or ""), str(item.get("document_name") or "")])
        )

    def _is_low_signal_context(self, item: dict) -> bool:
        content = str(item.get("content") or "").strip()
        if len(content) < 20:
            return True
        return bool(re.fullmatch(r"[\W\d\s]+", content))

    def _answer_declines_evidence(self, answer: str) -> bool:
        compact = self._normalize_query_text(answer)
        markers = (
            "资料中未找到明确依据",
            "未找到明确依据",
            # 回答已经声明检索资料没有明确对应内容时，不应再给出看似支持答案的参考来源。
            "没有找到明确的对应信息",
            "没有找到明确对应信息",
            "没有找到明确资料",
            "暂未找到明确资料",
            "无法确认",
            "无法回答",
        )
        return any(marker in compact for marker in markers)

    def _dedupe_terms(self, terms: list[str]) -> list[str]:
        deduped: list[str] = []
        for term in terms:
            if term and term not in deduped:
                deduped.append(term)
        return deduped

    def _threshold_score(self, item: dict) -> float:
        for key in ("combined_score", "rerank_score", "rrf_score", "score"):
            value = item.get(key)
            if value is not None:
                return float(value)
        return 0.0

    def _query_terms(self, query: str) -> list[str]:
        normalized = self._normalize_query_text(query)
        common_phrases = [
            "合同总价",
            "合同总价款",
            "合同总额",
            "合同总金额",
            "合同价",
            "合同金额",
            "合同价款",
            "项目金额",
            "服务费",
            "服务费用",
            "云租用服务费",
            "合同款项",
            "成交单价",
            "采购清单",
            "付款方式",
            "支付方式",
            "货款支付",
            "支付节点",
            "付款节点",
            "付款比例",
            "支付比例",
            "甲方",
            "乙方",
            "签署时间",
            "生效",
            "合同生效",
            "签字盖章",
            "违约责任",
            "保密条款",
            "保密责任",
            "保密期限",
            "保密有效期",
            "有效期",
            "知识产权",
            "数据产权",
            "争议解决",
            "人民法院",
            "仲裁",
            "服务项目",
            "质保期",
            "保修期",
            "质保金",
            "交货期",
            "交付期限",
            "合同内容",
            "项目概述",
            "价款结算",
            "合同款项总额",
            "实施周期",
            "项目建设周期",
            "服务期限",
            "服务的变更",
            "试运行",
            "终验",
        ]
        intent_expansions = {
            "总价": ["合同总价", "合同总价款", "合同价", "合同金额", "合同价款", "合同总额", "项目金额", "服务费用", "合同款项总额"],
            "金额": ["合同金额", "合同总金额", "合同总额", "合同总价", "合同总价款", "项目金额", "合同价款", "服务费用"],
            "合同价": ["合同价", "合同价款", "合同金额", "合同总价"],
            "价款": ["合同价款", "合同总价款", "合同金额"],
            "服务费": ["服务费", "服务费用", "云租用服务费", "租用服务费"],
            "付款": [
                "付款方式",
                "支付方式",
                "货款支付",
                "付款节点",
                "支付节点",
                "付款比例",
                "支付比例",
                "合同总价款",
                "合同总金额",
                "合同总额",
                "合同金额",
                "合同价款",
                "合同剩余款项",
                "支付",
                "增值税发票",
                "增值税专用发票",
            ],
            "支付": [
                "付款方式",
                "支付方式",
                "货款支付",
                "付款节点",
                "支付节点",
                "付款比例",
                "支付比例",
                "合同总价款",
                "合同总金额",
                "合同总额",
                "合同金额",
                "合同价款",
                "合同剩余款项",
                "支付",
                "增值税发票",
                "增值税专用发票",
            ],
            "保密": ["保密条款", "保密责任", "保密期限", "保密有效期", "有效期", "未经", "第三方", "书面许可", "永久保密", "持续有效"],
            "有效期": ["有效期", "保密有效期", "5年"],
            "争议": ["争议解决", "法律适用", "友好协商", "协商", "调解", "人民法院", "仲裁", "起诉"],
            "生效": ["合同生效", "其他条款", "签字盖章", "加盖公章", "合同专用章", "盖章", "生效"],
            "质保": ["质保期", "质保金", "保修期", "质量保证期"],
            "保修": ["保修期", "质保期", "质量保证期"],
            "交货": ["交货期", "交付期限", "交付", "验收合格"],
            "交付": ["交货期", "交付期限", "交付", "验收合格"],
            "周期": ["实施周期", "项目建设周期", "服务期限", "试运行", "终验"],
            "期限": ["服务期限", "保密期限", "质保期", "保修期", "试运行", "终验"],
            "终止": ["服务的变更", "终止", "继续存储", "存储", "数据", "30日内", "自行承担"],
            "验收": ["验收", "初验", "终验", "试运行"],
        }
        stop_phrases = [
            "请问",
            "是多少",
            "是什么",
            "有哪些",
            "如何约定",
            "如何解决",
            "如何处理",
            "如何计算",
            "多少",
            "哪",
            "谁",
            "吗",
            "呢",
            "的",
        ]
        terms: list[str] = []
        terms.extend(self._school_query_terms(normalized))
        marker_candidates = self._ranking_marker_candidates(common_phrases, intent_expansions)
        project_terms = self._project_terms_from_query(normalized, marker_candidates)
        terms.extend(project_terms)
        for phrase in common_phrases:
            if phrase in normalized:
                terms.append(phrase)
        for trigger, expansions in intent_expansions.items():
            if trigger in normalized:
                terms.extend(expansions)
        stripped = normalized
        for phrase in stop_phrases:
            stripped = stripped.replace(phrase, "")
        if len(stripped) >= 2:
            terms.append(stripped)
        if not terms and normalized:
            terms.append(normalized)
        deduped: list[str] = []
        for term in terms:
            if term and term not in deduped:
                deduped.append(term)
        return deduped

    def _school_query_terms(self, normalized: str) -> list[str]:
        if not normalized:
            return []
        terms: list[str] = []
        direct_phrases = [
            "参赛要求",
            "活动时间",
            "活动地点",
            "比赛项目",
            "活动流程",
            "比赛细则",
            "报名办法",
            "报名要求",
            "奖项设置",
            "体能五项",
            "健康测试",
            "体育文化节",
        ]
        for phrase in direct_phrases:
            if phrase in normalized:
                terms.append(phrase)

        for suffix in ("比赛", "活动", "讲座", "测试", "通知", "报名表", "项目"):
            pattern = rf"[\u4e00-\u9fffA-Za-z0-9]{{2,18}}{suffix}"
            for match in re.finditer(pattern, normalized):
                value = match.group(0)
                terms.append(value)
                for length in (4, 6, 8, 10):
                    if len(value) >= length:
                        terms.append(value[-length:])

        intent_markers = [
            "什么时候",
            "什么时间",
            "何时",
            "开始",
            "参赛要求",
            "要求",
            "规则",
            "条件",
            "流程",
            "地点",
        ]
        stop_words = (
            "请问",
            "关于",
            "这个",
            "那个",
            "是什么",
            "有哪些",
            "怎么",
            "如何",
            "以及",
            "和",
            "的",
        )
        for marker in intent_markers:
            position = normalized.find(marker)
            if position <= 0:
                continue
            prefix = normalized[:position]
            for word in stop_words:
                prefix = prefix.replace(word, "")
            prefix = prefix.strip()
            if len(prefix) >= 2:
                terms.append(prefix)
                for length in (4, 6, 8, 10):
                    if len(prefix) >= length:
                        terms.append(prefix[-length:])

        if "拔河" in normalized:
            terms.extend(["拔河", "拔河比赛"])

        deduped: list[str] = []
        for term in terms:
            clean = term.strip()
            if clean and clean not in deduped:
                deduped.append(clean)
        return deduped

    def _normalize_query_text(self, query: str) -> str:
        normalized = re.sub(r"\s+", "", query)
        return re.sub(r"[?？,，。.!！:：;；“”\"'（）()【】\[\]《》<>]", "", normalized)

    def _ranking_marker_candidates(
        self,
        common_phrases: list[str] | None = None,
        intent_expansions: dict[str, list[str]] | None = None,
    ) -> list[str]:
        common = common_phrases or [
            "合同总价",
            "合同总价款",
            "合同总额",
            "合同总金额",
            "合同价",
            "合同金额",
            "合同价款",
            "付款方式",
            "支付方式",
            "货款支付",
            "保密条款",
            "保密有效期",
            "有效期",
            "争议解决",
            "合同生效",
            "服务费",
            "服务费用",
            "云租用服务费",
            "质保期",
            "保修期",
            "交货期",
            "服务的变更",
        ]
        intents = list((intent_expansions or {}).keys()) or [
            "总价",
            "金额",
            "价款",
            "付款",
            "支付",
            "保密",
            "争议",
            "生效",
            "质保",
            "保修",
            "交货",
            "交付",
            "周期",
            "期限",
            "终止",
            "验收",
        ]
        return common + intents + [
            "付款比例",
            "付款节点",
            "支付比例",
            "支付节点",
            "合同款项",
            "款项总额",
            "什么时候",
            "多久",
        ]

    def _project_terms_from_query(self, normalized: str, markers: list[str]) -> list[str]:
        marker_positions = [normalized.find(marker) for marker in markers if marker in normalized]
        if not marker_positions:
            return []
        project = normalized[: min(marker_positions)]
        project = re.sub(r"(请问|关于|什么时候|什么时间|多久|如何|怎么|完成|以及|和|与)", "", project)
        project = re.sub(
            r"(请问|关于|项目|合同|服务|采购|建设|系统|平台|工程|子项目|什么|多少|如何|是谁|是)$",
            "",
            project,
        )
        project = project.strip("的是")
        if len(project) < 4:
            return []
        terms = [project]
        terms.extend(self._project_entity_terms(project))
        pieces = re.split(r"(?:项目|合同|服务|采购|建设|系统|平台|工程|子项目|一期|二期|及|\+)", project)
        for piece in pieces:
            piece = piece.strip("年月日的一二三四五六七八九十")
            if len(piece) >= 4:
                terms.append(piece)
        # 合同问题经常把有区分度的项目名放在末尾，因此补充一个短后缀。
        if len(project) > 8:
            terms.append(project[-8:])
        return terms

    def _project_entity_terms(self, project: str) -> list[str]:
        terms: list[str] = []
        suffixes = [
            "有限公司",
            "职业学院",
            "第一附属医院",
            "附属医院",
            "管理厅",
            "集团",
            "医院",
            "学院",
            "公司",
            "大学",
            "厅",
            "院",
        ]
        for suffix in suffixes:
            for match in re.finditer(re.escape(suffix), project):
                entity = project[: match.end()]
                if len(entity) >= 4:
                    terms.append(entity)
                tail = project[match.end() :]
                tail = re.sub(r"^(?:20\d{2}年)?(?:上半年|下半年)?", "", tail)
                tail = re.sub(r"(?:项目|合同|服务|采购|建设|系统|平台|工程|子项目)$", "", tail)
                tail = re.sub(r"(?:一期|二期|三期)$", "", tail)
                tail = tail.strip("年月日的一二三四五六七八九十")
                if len(tail) >= 4:
                    terms.append(tail)
        return terms

    def _citations(self, results: list[dict], query: str | None = None, answer: str | None = None) -> list[dict]:
        seen: dict[str, dict] = {}
        for item in results:
            if self._is_invalid_document_source(item):
                continue
            document_id = item.get("document_id")
            qa_pair_id = item.get("qa_pair_id")
            tags = item.get("tags") or []
            # 问答对可以不绑定来源文档，此时来源文档编号和链接都可能为空；仍需保留引用，前端才能在问答详情里展示绑定标签。
            if not document_id and not qa_pair_id:
                continue
            url = item.get("url") or ("/qa-pairs" if qa_pair_id else None)
            citation_key = self._citation_key(item)
            if citation_key in seen:
                self._merge_citation_location(seen[citation_key], item)
                self._merge_citation_images(seen[citation_key], item)
                continue
            seen[citation_key] = {
                "document_id": str(document_id) if document_id else None,
                "document_title": self._display_document_title(item),
                "document_name": self._original_download_name(item) or self._display_document_title(item),
                "chunk_id": str(item.get("chunk_id")) if item.get("chunk_id") else None,
                "qa_pair_id": str(qa_pair_id) if qa_pair_id else None,
                "page_start": item.get("page_start"),
                "page_end": item.get("page_end"),
                "section_path": item.get("section_path"),
                "page_numbers": [],
                "table_numbers": [],
                "section_paths": [],
                "location_label": "",
                "url": url,
                "tags": tags,
                "images": [],
            }
            self._merge_citation_location(seen[citation_key], item)
            self._merge_citation_images(seen[citation_key], item)
        return list(seen.values())[: self.MAX_CITATION_ITEMS]

    def _filter_invalid_document_sources(self, results: list[dict], stage: str | None = None) -> list[dict]:
        if not results:
            return results
        return [item for item in results if not self._is_invalid_document_source(item)]

    def _is_invalid_document_source(self, item: dict) -> bool:
        for key in ("document_name", "file_name", "document_title", "title"):
            if self._has_legacy_url_encoded_name(item.get(key)):
                return True
            if self._has_blacklisted_document_name(item.get(key)):
                return True
        return False

    def _load_blacklist_keywords(self) -> list[str]:
        raw = str(getattr(self.settings, "retrieval_blacklist_keywords", "") or "")
        configured = [item.strip() for item in re.split(r"[,，\n;；]+", raw) if item.strip()]
        keywords = configured or list(self.DEFAULT_BLACKLIST_KEYWORDS)
        deduped: list[str] = []
        for keyword in keywords:
            normalized = re.sub(r"\s+", "", keyword).lower()
            if not normalized or normalized in deduped:
                continue
            deduped.append(normalized)
        return deduped

    def _blacklist_sql_patterns(self) -> list[str]:
        return [f"%{keyword}%" for keyword in self.blacklist_keywords] or ["__rag_no_blacklist_match__"]

    def _document_blacklist_sql(self) -> str:
        haystack = (
            "regexp_replace(lower(COALESCE(d.title, '') || ' ' || COALESCE(d.file_name, '') || ' ' "
            "|| COALESCE(d.source_url, '') || ' ' || COALESCE(d.preview_url, '') || ' ' "
            "|| COALESCE(d.download_url, '')), '\\s+', '', 'g')"
        )
        return f"{haystack} ILIKE ANY(CAST(:blacklist_keywords AS text[]))"

    def _has_blacklisted_document_name(self, value) -> bool:
        text = re.sub(r"\s+", "", str(value or "")).lower()
        if not text:
            return False
        return any(keyword in text for keyword in self.blacklist_keywords)

    def _has_legacy_url_encoded_name(self, value) -> bool:
        text = str(value or "").strip()
        if not text:
            return False
        file_name = re.split(r"[\\/]", text)[-1]
        return bool(self.LEGACY_URL_ENCODED_NAME_RE.search(file_name))

    def _citation_key(self, item: dict) -> str:
        # 问答引用按问答记录去重，避免同一来源文档下多条问答被合并后丢失各自绑定标签。
        if item.get("qa_pair_id"):
            return f"qa:{item.get('qa_pair_id')}"
        return f"document:{item.get('document_id')}"

    def _merge_citation_location(self, citation: dict, item: dict) -> None:
        pages = citation.setdefault("page_numbers", [])
        for page in self._citation_pages(item):
            if page not in pages:
                pages.append(page)
        pages.sort()

        table_numbers = citation.setdefault("table_numbers", [])
        for table in self._citation_tables(item):
            if table not in table_numbers:
                table_numbers.append(table)

        section_paths = citation.setdefault("section_paths", [])
        section = str(item.get("section_path") or "").strip()
        if section and section not in section_paths:
            section_paths.append(section)

        if pages:
            citation["page_start"] = pages[0]
            citation["page_end"] = pages[-1]
        if table_numbers and not citation.get("section_path"):
            citation["section_path"] = "、".join(table_numbers[:3])
        citation["location_label"] = self._citation_location_label(citation)

    def _citation_pages(self, item: dict) -> list[int]:
        pages: list[int] = []
        for key in ("page_start", "page_end"):
            value = item.get(key)
            if isinstance(value, int) and value > 0 and value not in pages:
                pages.append(value)
        if len(pages) == 2 and pages[1] > pages[0] + 1 and pages[1] - pages[0] <= 20:
            return list(range(pages[0], pages[1] + 1))
        return pages

    def _citation_tables(self, item: dict) -> list[str]:
        candidates = [
            item.get("section_path"),
            item.get("document_title"),
            item.get("document_name"),
            item.get("file_name"),
            str((item.get("metadata") or {}).get("table_title") or ""),
        ]
        tables: list[str] = []
        for value in candidates:
            text = str(value or "")
            for match in re.finditer(r"表格?\s*([0-9一二三四五六七八九十]+)", text):
                label = f"表格 {match.group(1)}"
                if label not in tables:
                    tables.append(label)
        return tables

    def _citation_location_label(self, citation: dict) -> str:
        parts: list[str] = []
        pages = citation.get("page_numbers") or []
        if pages:
            parts.append(f"第 {self._format_number_ranges(pages)} 页")
        tables = citation.get("table_numbers") or []
        if tables:
            parts.append("、".join(tables[:5]))
        return "，".join(parts)

    def _format_number_ranges(self, numbers: list[int]) -> str:
        ordered = sorted({number for number in numbers if isinstance(number, int) and number > 0})
        if not ordered:
            return ""
        ranges: list[str] = []
        start = previous = ordered[0]
        for number in ordered[1:]:
            if number == previous + 1:
                previous = number
                continue
            ranges.append(str(start) if start == previous else f"{start}-{previous}")
            start = previous = number
        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        return "、".join(ranges)

    def _citation_evidence(self, item: dict, query: str | None = None, answer: str | None = None) -> str:
        text = self._clean_citation_text(str(item.get("content") or item.get("qa_answer") or ""))
        if not text:
            return ""
        terms = self._citation_terms(query, answer)
        return self._evidence_window(text, terms, self.CITATION_EVIDENCE_CHARS)

    def _clean_citation_text(self, text: str) -> str:
        cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
        cleaned = re.sub(r"```.*?```", " ", cleaned, flags=re.S)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    def _citation_terms(self, query: str | None, answer: str | None) -> list[str]:
        terms: list[str] = []
        if query:
            terms.extend(self._meaningful_query_terms(query))
        if answer:
            normalized_answer = self._normalize_query_text(answer)
            terms.extend(self._number_terms(answer))
            terms.extend(self._answer_terms(normalized_answer)[:12])
        return sorted(self._dedupe_terms(terms), key=len, reverse=True)

    def _evidence_window(self, text: str, terms: list[str], limit: int) -> str:
        if len(text) <= limit:
            return text
        start = 0
        for term in terms:
            if not term:
                continue
            index = text.find(term)
            if index >= 0:
                start = max(0, index - max(24, limit // 4))
                break
        end = min(len(text), start + limit)
        if end - start < limit:
            start = max(0, end - limit)
        snippet = text[start:end].strip()
        if start > 0:
            snippet = f"...{snippet}"
        if end < len(text):
            snippet = f"{snippet}..."
        return snippet

    def _normalize_result(self, item: dict) -> dict:
        normalized = self._json_safe(item)
        normalized["document_title"] = self._display_document_title(normalized)
        normalized["url"] = self._result_url(normalized)
        normalized["images"] = self._result_images(normalized)
        return normalized

    def _merge_citation_images(self, citation: dict, item: dict) -> None:
        images = citation.setdefault("images", [])
        seen = {image.get("url") for image in images if image.get("url")}
        for image in item.get("images") or self._result_images(item):
            url = image.get("url")
            if not url or url in seen:
                continue
            images.append(image)
            seen.add(url)

    def _result_images(self, item: dict) -> list[dict]:
        metadata = item.get("metadata") or item.get("metadata_") or {}
        if not isinstance(metadata, dict):
            return []
        bucket = metadata.get("image_bucket")
        object_key = metadata.get("image_object_key")
        if not bucket or not object_key:
            return []
        try:
            url = self.minio_service.proxy_url(str(bucket), str(object_key))
        except Exception:
            return []
        return [
            {
                "image_id": metadata.get("image_id"),
                "image_index": metadata.get("image_index"),
                "url": url,
                "file_name": metadata.get("image_file_name"),
                "context_text": metadata.get("image_context"),
            }
        ]

    def _result_url(self, item: dict) -> str | None:
        bucket = item.get("storage_bucket")
        object_key = item.get("storage_object_key")
        if bucket and object_key:
            try:
                download_name = self._original_download_name(item)
                return self.minio_service.proxy_url(
                    str(bucket),
                    str(object_key),
                    download_name=str(download_name) if download_name else None,
                )
            except Exception:
                pass
        explicit_url = item.get("qa_source_url") or item.get("source_url")
        if explicit_url:
            return str(explicit_url)
        return item.get("url") or item.get("preview_url") or item.get("download_url")

    def _display_document_title(self, item: dict) -> str | None:
        title = item.get("document_title")
        file_name = item.get("document_name") or item.get("file_name")
        if not title:
            return file_name
        text = str(title)
        if text.count("?") >= max(2, len(text) // 2):
            return str(file_name) if file_name else text
        return text

    def _original_download_name(self, item: dict) -> str | None:
        for key in ("document_name", "file_name", "document_title"):
            value = str(item.get(key) or "").strip()
            if value:
                return value
        return None

    def _json_safe(self, item):
        return to_jsonable(item)

    async def _get_cached_retrieval(
        self,
        query: str,
        top_k: int,
        options: dict,
        *,
        corpus_version: dict | None = None,
    ) -> dict | None:
        if not self.settings.retrieval_cache_enabled:
            return None
        try:
            cache_key = await self._retrieval_cache_key(
                query,
                top_k,
                options,
                corpus_version=corpus_version,
            )
            cached = await self.redis_service.get_json(cache_key)
            return cached if isinstance(cached, dict) else None
        except Exception:
            return None

    async def _set_cached_retrieval(
        self,
        query: str,
        top_k: int,
        options: dict,
        result: dict,
        *,
        corpus_version: dict | None = None,
    ) -> None:
        if not self.settings.retrieval_cache_enabled:
            return
        ttl = max(1, self.settings.retrieval_cache_ttl_seconds)
        try:
            cache_key = await self._retrieval_cache_key(
                query,
                top_k,
                options,
                corpus_version=corpus_version,
            )
            await self.redis_service.set_json(cache_key, result, ttl=ttl)
        except Exception:
            return

    async def _retrieval_cache_key(
        self,
        query: str,
        top_k: int,
        options: dict,
        *,
        corpus_version: dict | None = None,
    ) -> str:
        corpus_version = corpus_version if corpus_version is not None else await self._corpus_version()
        payload = to_jsonable(
            {
                "embedding_model": self.settings.embedding_model,
                "rerank_model": self.settings.rerank_model,
                "retrieval_logic_version": 13,
                "top_k": top_k,
                "query": query,
                "options": options,
                "rag_settings": self.rag_settings,
                "corpus_version": corpus_version,
            }
        )
        raw = repr(payload)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"retrieval:{digest}"

    async def _corpus_version(self, db: AsyncSession | None = None) -> dict:
        sql = text(
            """
            SELECT stats.document_count,
                   stats.latest_document_update,
                   COALESCE(k.version, 0) AS knowledge_base_version,
                   COALESCE(k.changed_at, stats.latest_document_update) AS latest_knowledge_update
            FROM (
              SELECT count(*) AS document_count,
                     COALESCE(max(updated_at), 'epoch'::timestamptz) AS latest_document_update
              FROM documents
              WHERE deleted_at IS NULL
            ) AS stats
            LEFT JOIN knowledge_base_versions k ON k.scope = 'default'
            """
        )
        if db is not None:
            row = await db.execute(sql)
            data = row.one()._mapping
        else:
            async with AsyncSessionLocal() as local_db:
                row = await local_db.execute(sql)
                data = row.one()._mapping
        return {
            "document_count": int(data["document_count"] or 0),
            "latest_document_update": str(data["latest_document_update"]),
            "knowledge_base_version": int(data["knowledge_base_version"] or 0),
            "latest_knowledge_update": str(data["latest_knowledge_update"]),
        }
