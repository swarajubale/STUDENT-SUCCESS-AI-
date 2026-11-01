import pandas as pd


def calculate_attendance(data):
    """Calculate attendance percentage for every student and subject."""

    data = data.copy()

    data["attendance_percentage"] = (
        data["classes_attended"] / data["classes_held"]
    ) * 100

    return data


def calculate_assignment_completion(data):
    """Calculate assignment submission percentage."""

    data = data.copy()

    data["assignment_percentage"] = (
        data["assignments_submitted"] / data["assignments_total"]
    ) * 100

    return data


def calculate_overall_performance(data):
    """Calculate average quiz and exam performance."""

    data = data.copy()

    data["overall_performance"] = (
        data["quiz_average"] + data["exam_score"]
    ) / 2

    return data


def generate_analytics(data):
    """Run all academic calculations."""

    data = calculate_attendance(data)
    data = calculate_assignment_completion(data)
    data = calculate_overall_performance(data)

    return data


if __name__ == "__main__":
    from data_loader import load_student_data

    records = load_student_data()
    results = generate_analytics(records)

    print("\nSTUDENT SUCCESS AI - ANALYTICS ENGINE")
    print("=" * 45)

    print(results[
        [
            "student_id",
            "subject",
            "attendance_percentage",
            "assignment_percentage",
            "overall_performance"
        ]
    ].round(2).to_string(index=False))