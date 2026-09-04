from dataclasses import dataclass


@dataclass
class PolicyResult:
    allowed: bool
    status: str
    reason: str
    requires_human: bool


class PolicyEngine:

    MAX_AUTO_RETRY_AMOUNT = 10000
    MAX_RETRIES = 2
    MIN_RETRY_PROBABILITY = 0.70

    TEMPORARY_FAILURES = {
        "BANK_TIMEOUT",
        "NETWORK_ERROR"
    }

    PERMANENT_FAILURES = {
        "CARD_EXPIRED"
    }

    def check(
        self,
        action,
        amount,
        failure_reason,
        retry_count,
        recovery_probability
    ):

        # ---------------------------------------------------------
        # RULE 1: Never retry permanent failures
        # ---------------------------------------------------------
        if action == "RETRY" and failure_reason in self.PERMANENT_FAILURES:
            return PolicyResult(
                allowed=False,
                status="BLOCKED",
                reason="Permanent payment failure cannot be retried.",
                requires_human=False
            )

        # ---------------------------------------------------------
        # RULE 2: Automatic retry only for temporary failures
        # ---------------------------------------------------------
        if action == "RETRY" and failure_reason not in self.TEMPORARY_FAILURES:
            return PolicyResult(
                allowed=False,
                status="BLOCKED",
                reason="Automatic retry is restricted to temporary failures.",
                requires_human=False
            )

        # ---------------------------------------------------------
        # RULE 3: High-value automatic retries require human review
        # ---------------------------------------------------------
        if action == "RETRY" and amount > self.MAX_AUTO_RETRY_AMOUNT:
            return PolicyResult(
                allowed=False,
                status="ESCALATED",
                reason="High-value payment requires human review before retry.",
                requires_human=True
            )

        # ---------------------------------------------------------
        # RULE 4: Maximum retry limit
        # ---------------------------------------------------------
        if action == "RETRY" and retry_count >= self.MAX_RETRIES:
            return PolicyResult(
                allowed=False,
                status="STOPPED",
                reason="Maximum automatic retry limit reached.",
                requires_human=False
            )

        # ---------------------------------------------------------
        # RULE 5: Minimum ML confidence for automatic retry
        # ---------------------------------------------------------
        if action == "RETRY" and recovery_probability < self.MIN_RETRY_PROBABILITY:
            return PolicyResult(
                allowed=False,
                status="ESCALATED",
                reason="Recovery probability is below automatic retry threshold.",
                requires_human=True
            )

        # ---------------------------------------------------------
        # RULE 5.5: VALID RETRY -> APPROVE
        # ---------------------------------------------------------
        if action == "RETRY":
            return PolicyResult(
                allowed=True,
                status="APPROVED",
                reason="Retry satisfies all automatic recovery policy requirements.",
                requires_human=False
            )

        # ---------------------------------------------------------
        # RULE 6: Human review
        # ---------------------------------------------------------
        if action == "HUMAN_REVIEW":
            return PolicyResult(
                allowed=False,
                status="ESCALATED",
                reason="Payment requires human review.",
                requires_human=True
            )

        # ---------------------------------------------------------
        # RULE 7: Stop
        # ---------------------------------------------------------
        if action == "STOP":
            return PolicyResult(
                allowed=False,
                status="STOPPED",
                reason="Recovery action stopped by decision policy.",
                requires_human=False
            )

        # ---------------------------------------------------------
        # RULE 8: Customer-facing recovery actions
        # ---------------------------------------------------------
        if action in {
            "PAYMENT_REMINDER",
            "UPDATE_PAYMENT_METHOD"
        }:
            return PolicyResult(
                allowed=True,
                status="APPROVED",
                reason="Customer-facing recovery action is permitted.",
                requires_human=False
            )

        # ---------------------------------------------------------
        # FAIL CLOSED
        # ---------------------------------------------------------
        return PolicyResult(
            allowed=False,
            status="BLOCKED",
            reason="Unknown recovery action. System fails closed for safety.",
            requires_human=True
        )


# ================================================================
# LOCAL TESTS
# ================================================================

if __name__ == "__main__":

    engine = PolicyEngine()

    print("\nTEST 1: Safe retry")
    result = engine.check(
        action="RETRY",
        amount=2000,
        failure_reason="BANK_TIMEOUT",
        retry_count=0,
        recovery_probability=0.91
    )
    print(result)

    print("\nTEST 2: High-value payment")
    result = engine.check(
        action="RETRY",
        amount=18000,
        failure_reason="BANK_TIMEOUT",
        retry_count=0,
        recovery_probability=0.91
    )
    print(result)

    print("\nTEST 3: Expired card")
    result = engine.check(
        action="RETRY",
        amount=2000,
        failure_reason="CARD_EXPIRED",
        retry_count=0,
        recovery_probability=0.91
    )
    print(result)

    print("\nTEST 4: Too many retries")
    result = engine.check(
        action="RETRY",
        amount=2000,
        failure_reason="BANK_TIMEOUT",
        retry_count=2,
        recovery_probability=0.91
    )
    print(result)

    print("\nTEST 5: Low probability")
    result = engine.check(
        action="RETRY",
        amount=2000,
        failure_reason="BANK_TIMEOUT",
        retry_count=0,
        recovery_probability=0.55
    )
    print(result)