from typing import List


def explain_prediction(
    prediction: str,
    confidence: float,
    factors: List[dict],
) -> dict:
    sorted_factors = sorted(factors, key=lambda x: x.get("weight", 0), reverse=True)
    top_factors = sorted_factors[:5]

    factor_details = []
    for f in top_factors:
        factor_details.append({
            "factor": f.get("factor", "Unknown"),
            "weight": f.get("weight", 0),
            "value": f.get("value", "N/A"),
            "description": f"Contributed {f.get('weight', 0) * 100:.0f}% to prediction",
        })

    reasoning_parts = [f"Prediction: {prediction}"]
    reasoning_parts.append(f"Confidence: {confidence * 100:.0f}%")
    reasoning_parts.append("Key factors:")
    for f in factor_details[:3]:
        reasoning_parts.append(f"  - {f['factor']}: {f['description']}")

    return {
        "prediction": prediction,
        "confidence": confidence,
        "factors": factor_details,
        "reasoning": " ".join(reasoning_parts),
        "recommended_action": "Review the identified factors and take appropriate response.",
    }


def explain_recommendation(recommendation: dict) -> dict:
    factors = recommendation.get("factors", [])
    sorted_factors = sorted(factors, key=lambda x: x.get("weight", 0), reverse=True)

    explanation_parts = [
        f"Recommendation: {recommendation.get('recommendation', 'N/A')}",
        f"Priority: {recommendation.get('priority', 'medium')}",
        f"Reason: {recommendation.get('reason', 'N/A')}",
    ]

    if sorted_factors:
        explanation_parts.append("Contributing factors:")
        for f in sorted_factors[:3]:
            explanation_parts.append(
                f"  - {f.get('factor', 'Unknown')}: weight {f.get('weight', 0) * 100:.0f}%"
            )

    return {
        "explanation": " ".join(explanation_parts),
        "factors": sorted_factors,
        "confidence": recommendation.get("confidence", 0.0),
    }
