
import pandas as pd


WEIGHTS = {
    "performance": 0.40,
    "attendance": 0.30,
    "assignments": 0.20,
    "trend": 0.10,
}


def generate_student_intelligence(data):
    """
    Calculate transparent, rule-based subject priority scores.
    Higher scores indicate a greater need for attention.
    """

    data = data.copy()

    priority_scores = []
    priority_levels = []
    priority_reasons = []

    for _, row in data.iterrows():
        concerns = []
        reasons = []

        performance = row.get("overall_performance")
        attendance = row.get("attendance_percentage")
        assignments = row.get("assignment_percentage")
        trend = row.get("performance_trend")

        if pd.notna(performance):
            concerns.append(
                (100 - float(performance), WEIGHTS["performance"])
            )
            if float(performance) < 50:
                reasons.append("Low academic performance")

        if pd.notna(attendance):
            concerns.append(
                (100 - float(attendance), WEIGHTS["attendance"])
            )
            if float(attendance) < 75:
                reasons.append("Attendance needs improvement")

        if pd.notna(assignments):
            concerns.append(
                (100 - float(assignments), WEIGHTS["assignments"])
            )
            if float(assignments) < 60:
                reasons.append("Assignment completion is low")

        trend_scores = {
            "Declining": 100,
            "Stable": 50,
            "Improving": 0,
        }

        if trend in trend_scores:
            concerns.append(
                (trend_scores[trend], WEIGHTS["trend"])
            )
            if trend == "Declining":
                reasons.append("Performance is declining")

        if not concerns:
            score = 0
            reasons.append("Insufficient data for priority calculation")
        else:
            total_weight = sum(weight for _, weight in concerns)

            score = sum(
                concern * weight
                for concern, weight in concerns
            ) / total_weight

        score = round(score, 2)

        if score <= 25:
            level = "Low"
        elif score <= 50:
            level = "Moderate"
        elif score <= 70:
            level = "High"
        else:
            level = "Urgent"

        if not reasons:
            reasons.append("No major concerns identified")

        priority_scores.append(score)
        priority_levels.append(level)
        priority_reasons.append("; ".join(reasons))

    data["priority_score"] = priority_scores
    data["priority_level"] = priority_levels
    data["priority_reasons"] = priority_reasons

    data["priority_rank"] = (
        data["priority_score"]
        .rank(method="dense", ascending=False)
        .astype(int)
    )

    return data


def get_intelligence_summary(data):
    """Generate an overall summary of student performance."""

    if data.empty:
        return {
            "strongest_subject": None,
            "weakest_subject": None,
            "top_priority_subject": None,
            "subjects_needing_attention": 0,
        }

    valid = data.dropna(subset=["overall_performance"])

    strongest = None
    weakest = None

    if not valid.empty:
        strongest = valid.loc[
            valid["overall_performance"].idxmax(), "subject"
        ]
        weakest = valid.loc[
            valid["overall_performance"].idxmin(), "subject"
        ]

    top_priority = data.loc[
        data["priority_score"].idxmax(), "subject"
    ]

    attention_count = data["priority_level"].isin(
        ["High", "Urgent"]
    ).sum()

    return {
        "strongest_subject": strongest,
        "weakest_subject": weakest,
        "top_priority_subject": top_priority,
        "subjects_needing_attention": int(attention_count),
    }
