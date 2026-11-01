import pandas as pd


def generate_recommendations(data):
    """Generate personalised recommendations for students."""

    data = data.copy()

    recommendations = []

    for _, row in data.iterrows():

        actions = []

        # Attendance analysis
        if row["attendance_percentage"] < 75:
            actions.append(
                "Improve attendance. Attend upcoming classes regularly."
            )

        # Assignment analysis
        if row["assignment_percentage"] < 70:
            actions.append(
                "Complete pending assignments and submit them on time."
            )

        # Academic performance analysis
        if row["overall_performance"] < 50:
            actions.append(
                "Academic performance is low. Revise fundamentals and seek help."
            )

        elif row["overall_performance"] < 70:
            actions.append(
                "Improve subject understanding through regular practice."
            )

        # Study hours analysis
        if row["study_hours_weekly"] < 5:
            actions.append(
                "Increase focused study time to at least 5 hours weekly."
            )

        if not actions:
            actions.append(
                "Good progress! Maintain your current study routine."
            )

        recommendations.append(" ".join(actions))

    data["recommendations"] = recommendations

    return data


if __name__ == "__main__":
    from data_loader import load_student_data
    from analytics import generate_analytics

    records = load_student_data()
    results = generate_analytics(records)
    results = generate_recommendations(results)

    print("\nSTUDENT SUCCESS AI - RECOMMENDATION ENGINE")
    print("=" * 55)

    for _, row in results.iterrows():
        print(f"\nStudent: {row['student_id']}")
        print(f"Subject: {row['subject']}")
        print(f"Recommendation: {row['recommendations']}")