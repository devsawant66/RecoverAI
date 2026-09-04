def explain_decision(
    amount,
    failure_reason,
    retry_count,
    customer_success_rate,
    recovery_probability,
    action
):

    reasons = []

    if failure_reason in [
        "BANK_TIMEOUT",
        "NETWORK_ERROR"
    ]:
        reasons.append(
            "Failure appears temporary."
        )

    if customer_success_rate >= 0.85:
        reasons.append(
            "Customer has a strong historical "
            "payment success rate."
        )

    if retry_count == 0:
        reasons.append(
            "No previous retry has been attempted."
        )

    if retry_count >= 2:
        reasons.append(
            "Retry limit has been reached."
        )

    if recovery_probability >= 0.70:
        reasons.append(
            "Predicted recovery probability "
            "is high."
        )

    if amount > 10000:
        reasons.append(
            "Payment amount requires additional "
            "approval."
        )

    return {
        "action": action,
        "recovery_probability":
            round(recovery_probability, 4),
        "reasons": reasons
    }