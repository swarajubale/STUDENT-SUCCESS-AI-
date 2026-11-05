
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
            performance = float(performance)
            concerns.append(
                (100 - performance, WEIGHTS["performance"])
            )
            reasons.append(
                f"Academic performance: {performance:.1f}%"
            )

        if pd.notna(attendance):
            attendance = float(attendance)
            concerns.append(
                (100 - attendance, WEIGHTS["attendance"])
            )
            reasons.append(
                f"Attendance: {attendance:.1f}%"
            )

        if pd.notna(assignments):
            assignments = float(assignments)
            concerns.append(
                (100 - assignments, WEIGHTS["assignments"])
            )
            reasons.append(
                f"Assignment completion: {assignments:.1f}%"
            )

        
        performance_change = row.get("performance_change")

        if pd.notna(performance_change):
            trend_concern = max(
                0,
                min(100, -float(performance_change) * 10)
            )

            concerns.append(
                (trend_concern, WEIGHTS["trend"])
            )

            reasons.append(
                f"Performance change: {float(performance_change):+.1f} percentage points"
            )
        else:
            reasons.append("Performance trend: Insufficient history")


        if not concerns:
            score = None
            level = "Insufficient Data"
            reasons.append("Not enough academic data to calculate priority")

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
        .astype("Int64")
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

    valid_priority = data.dropna(subset=["priority_score"])

    top_priority = (
        valid_priority.loc[
            valid_priority["priority_score"].idxmax(), "subject"
        ]
        if not valid_priority.empty else None
    )

    attention_count = data["priority_level"].isin(
        ["High", "Urgent"]
    ).sum()

    return {
        "strongest_subject": strongest,
        "weakest_subject": weakest,
        "top_priority_subject": top_priority,
        "subjects_needing_attention": int(attention_count),
    }
