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
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
import pandas as pd
import numpy as np


def _numeric(data, column):
    if column not in data.columns:
        return pd.Series(np.nan, index=data.index, dtype="float64")
    return pd.to_numeric(data[column], errors="coerce")


def _percentage(numerator, denominator):
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    result = pd.Series(np.nan, index=numerator.index, dtype="float64")
    valid = denominator > 0
    result.loc[valid] = numerator.loc[valid] / denominator.loc[valid] * 100
    return result.clip(0, 100)


def calculate_attendance(data):
    data = data.copy()
    data["attendance_percentage"] = _percentage(
        _numeric(data, "classes_attended"), _numeric(data, "classes_held")
    )
    return data


def calculate_assignment_completion(data):
    data = data.copy()
    data["assignment_percentage"] = _percentage(
        _numeric(data, "assignments_submitted"), _numeric(data, "assignments_total")
    )
    return data


def calculate_overall_performance(data):
    """Quiz and exam count equally; a single available score is still usable."""
    data = data.copy()
    quiz = _numeric(data, "quiz_average").clip(0, 100)
    exam = _numeric(data, "exam_score").clip(0, 100)
    data["overall_performance"] = pd.concat([quiz, exam], axis=1).mean(axis=1)
    return data


def calculate_risk(data):
    """Transparent subject risk bands; missing metrics are not treated as failures."""
    data = data.copy()
    attendance = _numeric(data, "attendance_percentage")
    assignments = _numeric(data, "assignment_percentage")
    performance = _numeric(data, "overall_performance")

    high = ((attendance < 60) | (assignments < 40) | (performance < 40)).fillna(False)
    medium = ((attendance < 75) | (assignments < 60) | (performance < 60)).fillna(False)
    data["risk_level"] = np.select([high, medium], ["High", "Medium"], default="Low")

    reasons = []
    for idx in data.index:
        parts = []
        for value, critical, warning, label in [
            (attendance.loc[idx], 60, 75, "attendance"),
            (assignments.loc[idx], 40, 60, "assignment completion"),
            (performance.loc[idx], 40, 60, "performance"),
        ]:
            if pd.notna(value) and value < critical:
                parts.append(f"{label} below {critical}%")
            elif pd.notna(value) and value < warning:
                parts.append(f"{label} below {warning}%")
        reasons.append("; ".join(parts) if parts else "No threshold-based warning detected")
    data["risk_reasons"] = reasons
    return data


def calculate_performance_trends(data, history=None):
    """
    Compare the two latest usable history snapshots per subject.
    `history` accepts a DataFrame or get_student_history() tuple rows.
    """
    data = data.copy()
    data["performance_change"] = np.nan
    data["performance_trend"] = "Insufficient history"
    if history is None:
        return data

    columns = [
        "subject", "classes_attended", "classes_held",
        "assignments_submitted", "assignments_total",
        "quiz_average", "exam_score", "study_hours_weekly", "recorded_at"
    ]
    history_data = history.copy() if isinstance(history, pd.DataFrame) else pd.DataFrame(history, columns=columns)
    required = {"subject", "quiz_average", "exam_score", "recorded_at"}
    if history_data.empty or not required.issubset(history_data.columns):
        return data

    history_data["recorded_at"] = pd.to_datetime(history_data["recorded_at"], errors="coerce")
    for column in ["quiz_average", "exam_score"]:
        history_data[column] = pd.to_numeric(history_data[column], errors="coerce")

        history_data = history_data.dropna(subset=["recorded_at"])

    for idx, row in data.iterrows():
        subject_history = history_data[
            history_data["subject"] == row["subject"]
        ].sort_values("recorded_at")

        subject_history["snapshot_performance"] = subject_history[
            ["quiz_average", "exam_score"]
        ].mean(axis=1)

        usable = subject_history.dropna(subset=["snapshot_performance"])

        if len(usable) < 2:
            continue

        previous = usable.iloc[-2]["snapshot_performance"]
        latest = usable.iloc[-1]["snapshot_performance"]
        change = latest - previous

        data.at[idx, "performance_change"] = change

        if change >= 3:
            data.at[idx, "performance_trend"] = "Improving"
        elif change <= -3:
            data.at[idx, "performance_trend"] = "Declining"
        else:
            data.at[idx, "performance_trend"] = "Stable"

    return data


def generate_analytics(data, history=None):
    data = calculate_attendance(data)
    data = calculate_assignment_completion(data)
    data = calculate_overall_performance(data)
    data = calculate_risk(data)
    data = calculate_performance_trends(data, history)
    return data


def get_student_summary(data):
    return {
        "average_attendance": data["attendance_percentage"].mean(),
        "average_assignment_completion": data["assignment_completion"].mean(),
        "average_performance": data["overall_performance"].mean(),
        "high_risk_subjects": (data["risk_level"] == "High").sum(),
        "medium_risk_subjects": (data["risk_level"] == "Medium").sum(),
        "low_risk_subjects": (data["risk_level"] == "Low").sum(),
        "strongest_subject": (
            data.loc[data["overall_performance"].idxmax(), "subject"]
            if data["overall_performance"].notna().any() else None
        ),
        "weakest_subject": (
            data.loc[data["overall_performance"].idxmin(), "subject"]
            if data["overall_performance"].notna().any() else None
        ),
    }   