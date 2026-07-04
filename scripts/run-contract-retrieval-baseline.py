import argparse
import asyncio
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.services.retrieval_service import RetrievalService  # noqa: E402


def normalize(text: object) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def contains_any(haystack: str, terms: list[str]) -> bool:
    return any(normalize(term) in haystack for term in terms)


def display_title(item: dict) -> str:
    return str(item.get("document_title") or item.get("document_name") or "")


def context_doc_text(item: dict) -> str:
    return normalize(
        " ".join(
            [
                str(item.get("document_title") or ""),
                str(item.get("document_name") or ""),
                str(item.get("content") or ""),
            ]
        )
    )


def citation_doc_text(item: dict) -> str:
    return normalize(
        " ".join(
            [
                str(item.get("document_title") or ""),
                str(item.get("document_name") or ""),
                str(item.get("section_path") or ""),
                str(item.get("url") or ""),
            ]
        )
    )


def score_case(case: dict, trace: dict) -> dict:
    contexts = trace.get("final_context", [])
    citations = trace.get("citations", [])
    doc_terms = case.get("expected_document_terms", [])
    expected_terms = case.get("expected_terms", [])
    expected_pages = set(case.get("expected_pages", []))
    expected_section_terms = case.get("expected_section_terms", [])

    top1_doc_hit = bool(contexts) and contains_any(context_doc_text(contexts[0]), doc_terms)
    top3_doc_hit = any(contains_any(context_doc_text(item), doc_terms) for item in contexts[:3])
    context_text = normalize("\n".join(str(item.get("content") or "") for item in contexts))
    missing_terms = [term for term in expected_terms if normalize(term) not in context_text]

    if expected_pages:
        page_hit = any(item.get("page_start") in expected_pages for item in contexts)
    else:
        page_hit = True

    if expected_section_terms:
        section_text = normalize(
            "\n".join(
                " ".join([str(item.get("section_path") or ""), str(item.get("content") or "")])
                for item in contexts
            )
        )
        missing_sections = [
            term for term in expected_section_terms if normalize(term) not in section_text
        ]
        section_hit = not missing_sections
    else:
        missing_sections = []
        section_hit = True

    citation_doc_hit = any(contains_any(citation_doc_text(item), doc_terms) for item in citations)
    citation_usable = any(
        item.get("url") and (item.get("page_start") or item.get("section_path"))
        for item in citations
    )

    passed = (
        top3_doc_hit
        and not missing_terms
        and page_hit
        and section_hit
        and citation_doc_hit
        and citation_usable
    )
    return {
        "id": case["id"],
        "question": case["question"],
        "pass": passed,
        "top1_doc_hit": top1_doc_hit,
        "top3_doc_hit": top3_doc_hit,
        "terms_hit": not missing_terms,
        "page_hit": page_hit,
        "section_hit": section_hit,
        "citation_doc_hit": citation_doc_hit,
        "citation_usable": citation_usable,
        "missing_terms": missing_terms,
        "missing_section_terms": missing_sections,
        "top1_source": contexts[0].get("source") if contexts else None,
        "top_contexts": [
            {
                "document_title": display_title(item),
                "page_start": item.get("page_start"),
                "section_path": item.get("section_path"),
                "source": item.get("source"),
                "combined_score": item.get("combined_score"),
                "preview": str(item.get("content") or "")[:220].replace("\n", " "),
            }
            for item in contexts[:3]
        ],
        "citations": citations,
    }


async def run(cases: list[dict], top_k: int) -> list[dict]:
    service = RetrievalService()
    results = []
    async with AsyncSessionLocal() as db:
        for case in cases:
            trace = await service.search(db, case["question"], top_k=top_k)
            results.append(score_case(case, trace))
    return results


def summarize(results: list[dict]) -> dict:
    total = len(results)

    def ratio(key: str) -> dict:
        count = sum(1 for item in results if item.get(key))
        return {"count": count, "total": total, "rate": round(count / total, 4) if total else 0}

    return {
        "total": total,
        "pass": ratio("pass"),
        "top1_doc_hit": ratio("top1_doc_hit"),
        "top3_doc_hit": ratio("top3_doc_hit"),
        "terms_hit": ratio("terms_hit"),
        "page_hit": ratio("page_hit"),
        "section_hit": ratio("section_hit"),
        "citation_doc_hit": ratio("citation_doc_hit"),
        "citation_usable": ratio("citation_usable"),
        "qa_top1": {
            "count": sum(1 for item in results if item.get("top1_source") == "qa"),
            "total": total,
        },
    }


def write_markdown(path: Path, summary: dict, results: list[dict]) -> None:
    lines = [
        "# 合同检索基线评测报告",
        "",
        "评测范围：只评检索证据，不评生成答案。",
        "",
        "## 指标",
        "",
    ]
    for key in [
        "pass",
        "top1_doc_hit",
        "top3_doc_hit",
        "terms_hit",
        "page_hit",
        "section_hit",
        "citation_doc_hit",
        "citation_usable",
    ]:
        item = summary[key]
        lines.append(f"- {key}: {item['count']}/{item['total']} ({item['rate']:.2%})")
    lines.append(f"- qa_top1: {summary['qa_top1']['count']}/{summary['qa_top1']['total']}")
    lines.extend(["", "## 失败样本", ""])
    failures = [item for item in results if not item["pass"]]
    if not failures:
        lines.append("无。")
    for item in failures:
        lines.append(f"### {item['id']}")
        lines.append("")
        lines.append(f"- 问题：{item['question']}")
        lines.append(f"- top1_doc_hit: {item['top1_doc_hit']}")
        lines.append(f"- top3_doc_hit: {item['top3_doc_hit']}")
        lines.append(f"- missing_terms: {', '.join(item['missing_terms']) or '无'}")
        lines.append(f"- missing_section_terms: {', '.join(item['missing_section_terms']) or '无'}")
        lines.append(f"- page_hit: {item['page_hit']}")
        lines.append(f"- citation_doc_hit: {item['citation_doc_hit']}")
        lines.append(f"- citation_usable: {item['citation_usable']}")
        for idx, context in enumerate(item["top_contexts"], start=1):
            lines.append(
                f"- top{idx}: {context['document_title']} p{context['page_start']} "
                f"{context['section_path']} [{context['source']}]"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases",
        default=str(ROOT / "docs" / "retrieval-badcases-contracts.json"),
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--out")
    parser.add_argument("--markdown-out")
    args = parser.parse_args()

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    results = await run(cases, args.top_k)
    payload = {"summary": summarize(results), "results": results}
    if args.out:
        Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown_out:
        write_markdown(Path(args.markdown_out), payload["summary"], results)
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
