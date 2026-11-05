
import math
import pandas as pd


def generate_recommendations(data):
    """Generate personal recommendations and weekly academic action plans."""
    result = data.copy()
    recommendations = []
    weekly_plans = []

    for _, row in result.iterrows():
        actions = []
        weekly = []

        attendance = pd.to_numeric(pd.Series([row.get("attendance_percentage")]), errors="coerce").iloc[0]
        assignments = pd.to_numeric(pd.Series([row.get("assignment_percentage")]), errors="coerce").iloc[0]
        performance = pd.to_numeric(pd.Series([row.get("overall_performance")]), errors="coerce").iloc[0]
        study_hours = pd.to_numeric(pd.Series([row.get("study_hours_weekly")]), errors="coerce").iloc[0]
        trend = row.get("performance_trend", "Insufficient history")

        if pd.notna(attendance):
            if attendance < 75:
                attended = pd.to_numeric(pd.Series([row.get("classes_attended")]), errors="coerce").iloc[0]
                held = pd.to_numeric(pd.Series([row.get("classes_held")]), errors="coerce").iloc[0]

                if pd.notna(attended) and pd.notna(held) and held > 0 and 0 <= attended <= held:
                    classes_needed = max(0, math.ceil((0.75 * held - attended) / 0.25))
                    urgency = "Urgent" if attendance < 60 else "Action needed"
                    actions.append(
                        f"{urgency}: attendance is {attendance:.1f}%. "
                        f"Attend the next {classes_needed} classes consecutively to reach 75%, "
                        "assuming each future class is added to the total."
                    )
                else:
                    actions.append(
                        f"Attendance is {attendance:.1f}%. Attend every upcoming class and verify your attendance records."
                    )
            else:
                actions.append("Attendance is on track. Maintain consistent class attendance.")
        else:
            actions.append("Add valid attendance figures so attendance can be assessed.")

        if pd.notna(assignments):
            if assignments < 70:
                submitted = pd.to_numeric(pd.Series([row.get("assignments_submitted")]), errors="coerce").iloc[0]
                total = pd.to_numeric(pd.Series([row.get("assignments_total")]), errors="coerce").iloc[0]

                if pd.notna(submitted) and pd.notna(total) and total >= submitted >= 0 and total > 0:
                    pending = int(total - submitted)
                    if pending > 0:
                        actions.append(
                            f"Assignment completion is {assignments:.1f}%. "
                            f"Complete the {pending} pending assignment(s) to reach full completion."
                        )
                    else:
                        actions.append("Check assignment records; completion is below target.")
                else:
                    actions.append(
                        f"Assignment completion is {assignments:.1f}%. Finish the nearest deadline first."
                    )
            else:
                actions.append("Assignment completion is on track. Maintain timely submissions.")
        else:
            actions.append("Add assignment totals and submissions to assess completion.")

        if pd.notna(performance):
            if performance < 60:
                actions.append(
                    f"Performance is {performance:.1f}%. Review quiz and exam mistakes and practise your two weakest topics."
                )
            elif performance < 75:
                actions.append(
                    f"Performance is {performance:.1f}%. Practise topics where you lost marks."
                )
            else:
                actions.append(
                    f"Performance is {performance:.1f}%. Maintain your results and attempt challenging practice questions."
                )
        else:
            actions.append("Add quiz or exam scores to assess academic performance.")

        if pd.notna(study_hours):
            if study_hours < 5:
                actions.append(
                    f"Current study time is {study_hours:.1f} hours/week. Work towards 5 focused hours weekly."
                )
            else:
                actions.append(
                    f"Your study time is {study_hours:.1f} hours/week. Maintain a consistent study routine."
                )

        change = pd.to_numeric(pd.Series([row.get("performance_change")]), errors="coerce").iloc[0]

        if trend == "Declining" and pd.notna(change):
            actions.append(
                f"Recent performance declined by {abs(change):.1f} percentage points. Review what changed."
            )
        elif trend == "Improving" and pd.notna(change):
            actions.append(
                f"Recent performance improved by {change:.1f} percentage points. Keep the habits that are working."
            )

        priority = row.get("priority_level")
        if priority in ("High", "Urgent"):
            actions.insert(0, f"Priority: {priority}. Work on this subject before lower-priority subjects.")

        if not actions:
            actions.append("Keep recording academic progress to receive more specific recommendations.")

        # Build measurable weekly tasks.
        if pd.notna(attendance):
            if attendance < 75:
                weekly.append("Attend every scheduled class this week.")
            else:
                weekly.append("Maintain attendance in every scheduled class.")

        if pd.notna(assignments):
            if assignments < 70:
                weekly.append("Complete at least one pending assignment, starting with the nearest deadline.")
            else:
                weekly.append("Review upcoming assignment deadlines and submit work on time.")

        if pd.notna(performance):
            if performance < 75:
                weekly.append("Complete two focused practice sessions on difficult topics.")
            else:
                weekly.append("Complete one challenging practice session to strengthen your understanding.")

        if pd.notna(study_hours):
            weekly_target = max(5, math.ceil(study_hours))
            weekly.append(f"Target {weekly_target} focused study hours this week.")

        if not weekly:
            weekly.append("Add academic records to generate measurable weekly targets.")

        recommendations.append(" ".join(actions))
        weekly_plans.append(weekly)

    result["recommendations"] = recommendations
    result["weekly_action_plan"] = weekly_plans

    return result
