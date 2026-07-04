import argparse
import asyncio
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.services.retrieval_service import RetrievalService  # noqa: E402


BAD_CASES = [
    {
        "id": "contract_total",
        "question": "合同总价是多少？",
        "expected_terms": ["80000", "捌万元整"],
        "expected_citation_terms": ["采购清单"],
    },
    {
        "id": "party_a",
        "question": "甲方是谁？",
        "expected_terms": ["江西省总工会"],
        "expected_citation_terms": ["sample_contract.pdf"],
    },
    {
        "id": "party_b",
        "question": "乙方是谁？",
        "expected_terms": ["江西电信信息产业有限公司"],
        "expected_citation_terms": ["sample_contract.pdf"],
    },
    {
        "id": "payment_terms",
        "question": "付款方式是什么？",
        "expected_terms": ["验收合格后15个工作日", "增值税发票"],
        "expected_citation_terms": ["sample_contract.pdf"],
    },
    {
        "id": "confidentiality",
        "question": "保密条款有什么要求？",
        "expected_terms": ["未经对方书面许可", "第三方"],
        "expected_citation_terms": ["保密条款"],
    },
    {
        "id": "dispute_resolution",
        "question": "争议解决方式是什么？",
        "expected_terms": ["友好协商", "人民法院"],
        "expected_citation_terms": ["sample_contract.pdf"],
    },
    {
        "id": "effective_date",
        "question": "合同什么时候生效？",
        "expected_terms": ["加盖公章", "合同专用章", "签字盖章"],
        "expected_citation_terms": ["sample_contract.pdf"],
    },
]


async def run(top_k: int) -> list[dict]:
    service = RetrievalService()
    results = []
    async with AsyncSessionLocal() as db:
        for case in BAD_CASES:
            trace = await service.search(db, case["question"], top_k=top_k)
            context_text = "\n".join(str(item.get("content") or "") for item in trace["final_context"])
            citation_text = "\n".join(
                " ".join(
                    [
                        str(item.get("document_title") or ""),
                        str(item.get("section_path") or ""),
                        str(item.get("url") or ""),
                    ]
                )
                for item in trace["citations"]
            )
            missing_terms = [term for term in case["expected_terms"] if term not in context_text]
            missing_citations = [
                term for term in case["expected_citation_terms"] if term not in citation_text
            ]
            results.append(
                {
                    "id": case["id"],
                    "question": case["question"],
                    "pass": not missing_terms and not missing_citations,
                    "missing_terms": missing_terms,
                    "missing_citation_terms": missing_citations,
                    "top_contexts": [
                        {
                            "document_title": item.get("document_title"),
                            "page_start": item.get("page_start"),
                            "section_path": item.get("section_path"),
                            "source": item.get("source"),
                            "combined_score": item.get("combined_score"),
                            "lexical_score": item.get("lexical_score"),
                            "noise_penalty": item.get("noise_penalty"),
                            "preview": str(item.get("content") or "")[:180].replace("\n", " "),
                        }
                        for item in trace["final_context"][:3]
                    ],
                    "citations": trace["citations"],
                }
            )
    return results


def print_report(results: list[dict], as_json: bool) -> None:
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    passed = sum(1 for item in results if item["pass"])
    print(f"retrieval badcases: {passed}/{len(results)} passed")
    for item in results:
        status = "PASS" if item["pass"] else "FAIL"
        print(f"\n[{status}] {item['id']} - {item['question']}")
        if item["missing_terms"]:
            print("  missing terms:", ", ".join(item["missing_terms"]))
        if item["missing_citation_terms"]:
            print("  missing citation terms:", ", ".join(item["missing_citation_terms"]))
        for idx, context in enumerate(item["top_contexts"], start=1):
            print(
                f"  {idx}. {context['document_title']} p{context['page_start']} "
                f"{context['section_path']} {context['source']} "
                f"score={context['combined_score']} noise={context['noise_penalty']}"
            )
            print(f"     {context['preview']}")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    print_report(await run(args.top_k), args.json)


if __name__ == "__main__":
    asyncio.run(main())
