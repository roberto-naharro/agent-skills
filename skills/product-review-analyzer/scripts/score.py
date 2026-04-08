#!/usr/bin/env python3
"""
Product Review Analyzer — Score Calculator

Usage:
    python score.py '<json_array>'

Example:
    python score.py '[{"reliability":"genuine","sentiment_score":3},
                      {"reliability":"suspicious","sentiment_score":-1}]'

Output: JSON with final_score (0–10), confidence, and stats.
"""

import sys
import json

WEIGHTS: dict[str, float] = {
    "genuine": 1.0,
    "suspicious": 0.5,
    "ai_generated": 0.25,
    "expert_media": 0.75,
}

CONFIDENCE_THRESHOLDS = {"alta": 15, "media": 7}


def compute_score(reviews: list[dict]) -> dict:
    valid = [r for r in reviews if r.get("reliability") in WEIGHTS]
    discarded = [r for r in reviews if r.get("reliability") not in WEIGHTS]

    if not valid:
        return {
            "error": "No valid reviews to score.",
            "final_score": None,
            "discarded_reviews": len(discarded),
            "total_reviews": len(reviews),
        }

    scorable = []
    for r in valid:
        score = r.get("sentiment_score")
        if score is None:
            continue
        if not isinstance(score, (int, float)) or score < -5 or score > 5:
            print(
                json.dumps(
                    {
                        "warning": f"Skipping review with out-of-range sentiment_score: {score!r}",
                        "source": r.get("source", "unknown"),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            continue
        scorable.append(r)

    if not scorable:
        return {
            "error": "No reviews with a sentiment score to compute.",
            "final_score": None,
            "discarded_reviews": len(discarded),
            "total_reviews": len(reviews),
        }

    weighted_sum = sum(
        r["sentiment_score"] * WEIGHTS[r["reliability"]] for r in scorable
    )
    weighted_count = sum(WEIGHTS[r["reliability"]] for r in scorable)

    if weighted_count == 0:
        return {"error": "Weighted count is zero.", "final_score": None}

    raw = weighted_sum / weighted_count  # −5 to +5
    final_score = round((raw + 5) / 10 * 10, 1)
    final_score = max(0.0, min(10.0, final_score))

    genuine_count = sum(1 for r in valid if r["reliability"] == "genuine")

    if genuine_count >= CONFIDENCE_THRESHOLDS["alta"]:
        confidence = "Alta"
    elif genuine_count >= CONFIDENCE_THRESHOLDS["media"]:
        confidence = "Media"
    else:
        confidence = "Baja"

    breakdown = {k: sum(1 for r in valid if r["reliability"] == k) for k in WEIGHTS}

    return {
        "final_score": final_score,
        "confidence": confidence,
        "raw_sentiment": round(raw, 2),
        "breakdown": breakdown,
        "discarded_reviews": len(discarded),
        "total_reviews": len(reviews),
        "warning": (
            "Menos de 7 reseñas genuinas — resultado poco fiable."
            if genuine_count < CONFIDENCE_THRESHOLDS["media"]
            else None
        ),
    }


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Pass reviews JSON as first argument."}))
        sys.exit(1)

    try:
        reviews = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"Invalid JSON: {exc}"}))
        sys.exit(1)

    result = compute_score(reviews)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
