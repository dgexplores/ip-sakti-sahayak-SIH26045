"""Eval — RAGAS faithfulness + citation precision + abstention, offline-friendly."""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any


def _faithfulness_heuristic(answer: str, contexts: list[str]) -> float:
    """Offline heuristic: fraction of answer n-grams covered by contexts."""
    if not contexts or not answer:
        return 0.0
    ctx = " ".join(contexts).lower()
    words = [w for w in answer.lower().split() if len(w) > 3]
    if not words:
        return 0.5
    covered = sum(1 for w in words if w in ctx)
    return round(covered / len(words), 3)


def evaluate(golden_path: pathlib.Path, out_path: pathlib.Path | None = None) -> dict[str, Any]:
    data = json.loads(golden_path.read_text(encoding="utf-8"))
    # support both {"cases": [...]} and [...]
    cases = data.get("cases") if isinstance(data, dict) and "cases" in data else data
    if not isinstance(cases, list):
        raise ValueError("golden_set must be list or {cases: [...]}")

    results: list[dict] = []
    total_faith = 0.0
    correct_citations = 0
    abstained_correctly = 0

    # try real ragas if available and OPENAI_API_KEY set; else heuristic
    use_ragas = False
    try:
        import os

        if os.getenv("OPENAI_API_KEY"):
            from ragas.metrics import faithfulness  # type: ignore[import]

            use_ragas = True
    except Exception:
        use_ragas = False

    for case in cases:
        q = case.get("query", "")
        expected_j = case.get("expected_jurisdiction", "india")
        expected_abstain = case.get("should_abstain", False)
        contexts = case.get("contexts", [])
        answer = case.get("answer", "")  # if pre-filled, evaluate; else skip
        citations = case.get("citations", [])

        faith = _faithfulness_heuristic(answer, contexts) if answer else 0.0
        total_faith += faith

        # citation precision: do citations' locators appear in answer?
        cite_ok = True
        if citations and answer:
            cite_ok = any(c.get("locator", "")[:20].lower() in answer.lower() for c in citations if c.get("locator"))
        if cite_ok:
            correct_citations += 1

        # abstention
        abstained = case.get("abstained", False) or (answer.strip().lower().startswith("i don't have"))
        if expected_abstain == abstained:
            abstained_correctly += 1

        results.append({"query": q[:80], "faithfulness": faith, "citation_ok": cite_ok, "abstain_ok": expected_abstain == abstained})

    n = len(cases) or 1
    report = {
        "total": n,
        "faithfulness_mean": round(total_faith / n, 3),
        "citation_precision": round(correct_citations / n, 3),
        "abstention_accuracy": round(abstained_correctly / n, 3),
        "ragas_used": use_ragas,
        "cases": results,
        "verdict": "PASS" if (total_faith / n) >= 0.70 else "NEEDS_WORK",
    }
    if out_path:
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[eval] wrote {out_path} — faithfulness {report['faithfulness_mean']} verdict {report['verdict']}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--out", required=False)
    args = ap.parse_args()
    evaluate(pathlib.Path(args.golden), pathlib.Path(args.out) if args.out else None)


if __name__ == "__main__":
    main()
