from dataclasses import dataclass


@dataclass
class RecoveryDecision:

    action: str
    status: str
    reason: str
    confidence: float
    requires_human: bool
    expected_recovery_value: float


class RecoveryDecisionEngine:

    # =========================================================
    # Recovery thresholds
    # =========================================================

    AUTO_RETRY_THRESHOLD = 0.70
    REMINDER_THRESHOLD = 0.45

    # High-value transactions receive additional caution.
    HIGH_VALUE_AMOUNT = 10000

    # Very high confidence can still receive a
    # customer-facing recovery intervention.
    HIGH_VALUE_CONFIDENCE = 0.80

    MAX_RETRIES = 2

    TEMPORARY_FAILURES = {
        "BANK_TIMEOUT",
        "NETWORK_ERROR"
    }

    # =========================================================
    # Main decision function
    # =========================================================

    def decide(
        self,
        amount: float,
        failure_reason: str,
        retry_count: int,
        recovery_probability: float
    ):

        expected_value = (
            amount *
            recovery_probability
        )

        # =====================================================
        # HARD SAFETY RULE
        # =====================================================

        # Never continue automated recovery after the maximum
        # number of retries.
        if retry_count >= self.MAX_RETRIES:

            return RecoveryDecision(
                action="STOP",
                status="BLOCKED",
                reason=(
                    "Maximum recovery attempts reached. "
                    "Further automated recovery is stopped."
                ),
                confidence=recovery_probability,
                requires_human=False,
                expected_recovery_value=0
            )

        # =====================================================
        # EXPIRED CARD
        # =====================================================

        # An expired card should never be retried.
        # Ask the customer to update the payment method.
        if failure_reason == "CARD_EXPIRED":

            return RecoveryDecision(
                action="UPDATE_PAYMENT_METHOD",
                status="APPROVED",
                reason=(
                    "Payment method has expired. "
                    "Customer should update the payment method "
                    "before attempting payment again."
                ),
                confidence=recovery_probability,
                requires_human=False,
                expected_recovery_value=expected_value
            )

        # =====================================================
        # TEMPORARY FAILURES
        # =====================================================

        if failure_reason in self.TEMPORARY_FAILURES:

            # -------------------------------------------------
            # High-value transaction
            # -------------------------------------------------

            if amount > self.HIGH_VALUE_AMOUNT:

                # Very high confidence:
                # customer-facing reminder is safer than
                # directly retrying a high-value payment.
                if (
                    recovery_probability
                    >= self.HIGH_VALUE_CONFIDENCE
                ):

                    return RecoveryDecision(
                        action="PAYMENT_REMINDER",
                        status="APPROVED",
                        reason=(
                            "High-value payment with strong "
                            "recovery probability. A customer-"
                            "facing recovery reminder is preferred "
                            "over automatic retry."
                        ),
                        confidence=recovery_probability,
                        requires_human=False,
                        expected_recovery_value=expected_value
                    )

                # Medium confidence:
                # human review.
                return RecoveryDecision(
                    action="HUMAN_REVIEW",
                    status="ESCALATED",
                    reason=(
                        "High-value payment requires additional "
                        "review before automated recovery."
                    ),
                    confidence=recovery_probability,
                    requires_human=True,
                    expected_recovery_value=expected_value
                )

            # -------------------------------------------------
            # Normal-value temporary failure
            # -------------------------------------------------

            if recovery_probability >= self.AUTO_RETRY_THRESHOLD:

                return RecoveryDecision(
                    action="RETRY",
                    status="APPROVED",
                    reason=(
                        "Temporary failure with high recovery "
                        "probability. Automatic retry is suitable."
                    ),
                    confidence=recovery_probability,
                    requires_human=False,
                    expected_recovery_value=expected_value
                )

            elif recovery_probability >= self.REMINDER_THRESHOLD:

                return RecoveryDecision(
                    action="PAYMENT_REMINDER",
                    status="APPROVED",
                    reason=(
                        "Temporary failure with moderate recovery "
                        "probability. Customer intervention is "
                        "preferred."
                    ),
                    confidence=recovery_probability,
                    requires_human=False,
                    expected_recovery_value=expected_value
                )

            else:

                return RecoveryDecision(
                    action="STOP",
                    status="BLOCKED",
                    reason=(
                        "Recovery probability is too low for "
                        "automated intervention."
                    ),
                    confidence=recovery_probability,
                    requires_human=False,
                    expected_recovery_value=0
                )

        # =====================================================
        # INSUFFICIENT FUNDS
        # =====================================================

        if failure_reason == "INSUFFICIENT_FUNDS":

            return RecoveryDecision(
                action="PAYMENT_REMINDER",
                status="APPROVED",
                reason=(
                    "Insufficient funds detected. Immediate "
                    "automatic retry may not help; customer "
                    "should retry after resolving the balance."
                ),
                confidence=recovery_probability,
                requires_human=False,
                expected_recovery_value=expected_value
            )

        # =====================================================
        # BANK DECLINED
        # =====================================================

        if failure_reason == "BANK_DECLINED":

            # Strong probability → customer-facing recovery.
            if recovery_probability >= 0.60:

                return RecoveryDecision(
                    action="PAYMENT_REMINDER",
                    status="APPROVED",
                    reason=(
                        "Bank-declined payment still shows "
                        "reasonable recovery potential. "
                        "Customer-facing recovery is preferred."
                    ),
                    confidence=recovery_probability,
                    requires_human=False,
                    expected_recovery_value=expected_value
                )

            # Lower confidence → human review.
            return RecoveryDecision(
                action="HUMAN_REVIEW",
                status="ESCALATED",
                reason=(
                    "Bank decline has insufficient confidence "
                    "for automated recovery."
                ),
                confidence=recovery_probability,
                requires_human=True,
                expected_recovery_value=expected_value
            )

        # =====================================================
        # UNKNOWN ERROR
        # =====================================================

        if failure_reason == "UNKNOWN_ERROR":

            # If there is reasonable recovery potential,
            # ask the customer to retry rather than silently
            # abandoning the transaction.
            if recovery_probability >= 0.55:

                return RecoveryDecision(
                    action="PAYMENT_REMINDER",
                    status="APPROVED",
                    reason=(
                        "Unknown failure with moderate recovery "
                        "potential. Customer-facing recovery "
                        "intervention is recommended."
                    ),
                    confidence=recovery_probability,
                    requires_human=False,
                    expected_recovery_value=expected_value
                )

            return RecoveryDecision(
                action="HUMAN_REVIEW",
                status="ESCALATED",
                reason=(
                    "Unknown failure with insufficient confidence "
                    "for automated recovery."
                ),
                confidence=recovery_probability,
                requires_human=True,
                expected_recovery_value=expected_value
            )

        # =====================================================
        # DEFAULT SAFE FALLBACK
        # =====================================================

        return RecoveryDecision(
            action="HUMAN_REVIEW",
            status="ESCALATED",
            reason=(
                "Unrecognized failure reason. "
                "Human review required for safe handling."
            ),
            confidence=recovery_probability,
            requires_human=True,
            expected_recovery_value=expected_value
        )


# =============================================================
# Local test
# =============================================================

if __name__ == "__main__":

    engine = RecoveryDecisionEngine()

    tests = [

        {
            "name": "Safe retry",
            "amount": 2000,
            "failure_reason": "BANK_TIMEOUT",
            "retry_count": 0,
            "recovery_probability": 0.91
        },

        {
            "name": "Medium probability",
            "amount": 2000,
            "failure_reason": "NETWORK_ERROR",
            "retry_count": 0,
            "recovery_probability": 0.55
        },

        {
            "name": "High-value payment",
            "amount": 18000,
            "failure_reason": "BANK_TIMEOUT",
            "retry_count": 0,
            "recovery_probability": 0.91
        },

        {
            "name": "Expired card",
            "amount": 2000,
            "failure_reason": "CARD_EXPIRED",
            "retry_count": 0,
            "recovery_probability": 0.90
        },

        {
            "name": "Too many retries",
            "amount": 2000,
            "failure_reason": "BANK_TIMEOUT",
            "retry_count": 2,
            "recovery_probability": 0.90
        },

        {
            "name": "Bank declined",
            "amount": 3000,
            "failure_reason": "BANK_DECLINED",
            "retry_count": 0,
            "recovery_probability": 0.65
        }
    ]

    print("\nRecoverAI Decision Engine Tests")
    print("=" * 60)

    for test in tests:

        decision = engine.decide(
            amount=test["amount"],
            failure_reason=test["failure_reason"],
            retry_count=test["retry_count"],
            recovery_probability=
                test["recovery_probability"]
        )

        print(
            f"\nTEST: {test['name']}"
        )

        print(
            f"Action: {decision.action}"
        )

        print(
            f"Status: {decision.status}"
        )

        print(
            f"Reason: {decision.reason}"
        )

        print(
            f"Confidence: "
            f"{decision.confidence:.2%}"
        )

        print(
            f"Human required: "
            f"{decision.requires_human}"
        )

        print(
            f"Expected recovery: "
            f"₹{decision.expected_recovery_value:,.2f}"
        )