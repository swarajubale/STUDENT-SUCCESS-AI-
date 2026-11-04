
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
import pandas as pd


def generate_recommendations(data):
    """Generate transparent, subject-specific actions from available indicators."""
    result = data.copy()
    recommendations = []

    for _, row in result.iterrows():
        actions = []
        attendance = pd.to_numeric(pd.Series([row.get("attendance_percentage")]), errors="coerce").iloc[0]
        assignments = pd.to_numeric(pd.Series([row.get("assignment_percentage")]), errors="coerce").iloc[0]
        performance = pd.to_numeric(pd.Series([row.get("overall_performance")]), errors="coerce").iloc[0]
        study_hours = pd.to_numeric(pd.Series([row.get("study_hours_weekly")]), errors="coerce").iloc[0]
        trend = row.get("performance_trend", "Insufficient history")

        if pd.notna(attendance):
            if attendance < 60:
                actions.append("Urgent: attendance is below 60%. Attend every upcoming class and check your institution's attendance rules.")
            elif attendance < 75:
                actions.append("Attendance is below 75%. Attend upcoming classes consistently.")
        else:
            actions.append("Add valid attendance figures so attendance can be assessed.")

        if pd.notna(assignments):
            if assignments < 40:
                actions.append("Assignment completion is critically low. Complete the nearest-deadline pending work first.")
            elif assignments < 70:
                actions.append("Improve assignment completion by setting a weekly submission target.")
        else:
            actions.append("Add assignment totals and submissions to assess completion.")

        if pd.notna(performance):
            if performance < 40:
                actions.append("Performance is very low. Revisit prerequisite concepts and seek help from a teacher or tutor.")
            elif performance < 60:
                actions.append("Review quiz and exam mistakes, then practise the weakest topics.")
            elif performance < 75:
                actions.append("Build consistency with focused practice and review topics where marks were lost.")
        else:
            actions.append("Add quiz or exam scores to assess academic performance.")

        if pd.notna(study_hours) and study_hours < 5:
            actions.append("Gradually increase focused study time towards at least 5 hours weekly, while protecting sleep and breaks.")

        change = row.get("performance_change")
        if trend == "Declining" and pd.notna(change):
            actions.append(f"Recent performance declined by {abs(change):.1f} percentage points. Review what changed.")
        elif trend == "Improving" and pd.notna(change):
            actions.append(f"Recent performance improved by {change:.1f} percentage points. Keep the habits that are working.")

        priority = row.get("priority_level")
        if priority in ("High", "Urgent"):
            actions.insert(0, f"Priority: {priority}. Address this subject before lower-priority subjects.")

        if not actions:
            actions.append("Available indicators look healthy. Maintain your routine and keep recording progress.")
        recommendations.append(" ".join(actions))

    result["recommendations"] = recommendations
    return result

