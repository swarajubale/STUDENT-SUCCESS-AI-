
import pandas as pd


def generate_study_plan(data):
    result = data.copy()

    result["study_hours_weekly"] = pd.to_numeric(
        result["study_hours_weekly"], errors="coerce"
    ).fillna(0).clip(lower=0)

    result["priority_score"] = pd.to_numeric(
        result["priority_score"], errors="coerce"
    ).fillna(0)

    result["recommended_study_hours"] = result["study_hours_weekly"]

    total_hours = result["study_hours_weekly"].sum()

    if total_hours <= 0 or len(result) < 2:
        result["hours_change"] = 0.0
        return result

    average_priority = result["priority_score"].mean()

    # Subjects above average priority need more attention.
    recipients = result["priority_score"] > average_priority
    donors = result["priority_score"] < average_priority

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
        result["recommended_study_hours"]
        - result["study_hours_weekly"]
    ).round(1)

    return result
