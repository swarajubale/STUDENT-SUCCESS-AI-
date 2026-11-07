
from unittest import result

import pandas as pd


def generate_study_plan(data):
    result = data.copy()

    result["study_hours_weekly"] = pd.to_numeric(
        result["study_hours_weekly"], errors="coerce"
    ).fillna(0).clip(lower=0)

    result["priority_score"] = pd.to_numeric(
    result["priority_score"], errors="coerce"
    )

    result["recommended_study_hours"] = result["study_hours_weekly"]
    result["hours_change"] = 0.0
    result["allocation_reason"] = "Current study time maintained."
    
    total_hours = result["study_hours_weekly"].sum()

    if total_hours <= 0 or len(result) < 2:
        result["hours_change"] = 0.0
        return result

    valid_priority = result["priority_score"].notna()

    average_priority = result.loc[
    valid_priority, "priority_score"
    ].mean()

    # Only subjects with valid priority scores can receive or donate hours.
    recipients = (
    valid_priority & (result["priority_score"] > average_priority)
    )
    donors = (
    valid_priority & (result["priority_score"] < average_priority)
    )

    # Redistribute up to 15% of total study time.
    transfer_pool = total_hours * 0.15

    donor_capacity = (
        result.loc[donors, "study_hours_weekly"] * 0.20
    )

    available_hours = donor_capacity.sum()
    transfer_pool = min(transfer_pool, available_hours)

    if recipients.any() and transfer_pool > 0:
        # Take hours proportionally from lower-priority subjects.
        if available_hours > 0:
            result.loc[donors, "recommended_study_hours"] -= (
                donor_capacity / available_hours * transfer_pool
            )

        # Give more hours to subjects with higher priority scores.
        recipient_weights = result.loc[recipients, "priority_score"]
        recipient_weights = recipient_weights - average_priority
        total_weight = recipient_weights.sum()

        if total_weight > 0:
            result.loc[recipients, "recommended_study_hours"] += (
                recipient_weights / total_weight * transfer_pool
            )

    result["recommended_study_hours"] = (
        result["recommended_study_hours"].round(1)
    )
    result["hours_change"] = (
    result["recommended_study_hours"] - result["study_hours_weekly"]
    ).round(1)

    def explain_allocation(row):
        change = row["hours_change"]
        reasons = row.get("priority_reasons", "")

        if change > 0:
            return f"Extra time allocated due to higher priority. {reasons}"
        elif change < 0:
            return "Some time redistributed to higher-priority subjects."
        return "Current study time maintained."

    result["allocation_reason"] = result.apply(explain_allocation, axis=1)

    return result

def generate_weekly_timetable(study_plan):
    days = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday"
    ]

    activities = [
        "Focused Learning",
        "Practice",
        "Revision",
        "Problem Solving",
        "Active Recall",
        "Mixed Practice"
    ]

    timetable = []

    for _, row in study_plan.iterrows():
        subject = row["subject"]
        weekly_hours = row["recommended_study_hours"]

        # Reserve 30 minutes for Sunday's subject test.
        weekday_hours = max(weekly_hours - 0.5, 0)
        daily_hours = weekday_hours / 6

        for i, day in enumerate(days):
            if daily_hours > 0:
                timetable.append({
                    "Day": day,
                    "Subject": subject,
                    "Activity": activities[i],
                    "Duration (hours)": round(daily_hours, 2)
                })

        # Sunday: 30-minute test for each subject.
        timetable.append({
            "Day": "Sunday",
            "Subject": subject,
            "Activity": "30-Minute Subject Test",
            "Duration (hours)": 0.5
        })

    return pd.DataFrame(timetable)