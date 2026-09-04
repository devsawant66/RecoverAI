import joblib
import pandas as pd

from agent.decision_engine import RecoveryDecisionEngine
from policy.policy_engine import PolicyEngine


MODEL_PATH = "models/recovery_model.pkl"

FEATURES = [
    "amount",
    "payment_method",
    "failure_reason",
    "retry_count",
    "previous_payment_count",
    "previous_success_count",
    "customer_success_rate",
    "days_since_last_payment",
    "customer_lifetime_value"
]


class RecoveryWorkflow:

    def __init__(self):

        self.model = joblib.load(MODEL_PATH)

        self.decision_engine = RecoveryDecisionEngine()

        self.policy_engine = PolicyEngine()

    def analyze_payment(self, payment):

        # ---------------------------------------------
        # 1. ML prediction
        # ---------------------------------------------

        input_df = pd.DataFrame([payment])

        recovery_probability = (
            self.model.predict_proba(
                input_df[FEATURES]
            )[0][1]
        )

        amount = float(payment["amount"])

        expected_recovery_value = (
            amount * recovery_probability
        )

        # ---------------------------------------------
        # 2. Decision Engine
        # ---------------------------------------------

        decision = self.decision_engine.decide(
            amount=amount,
            failure_reason=payment["failure_reason"],
            retry_count=int(payment["retry_count"]),
            recovery_probability=recovery_probability
        )

        # ---------------------------------------------
        # 3. Policy Engine
        # ---------------------------------------------

        policy = self.policy_engine.check(
            action=decision.action,
            amount=amount,
            failure_reason=payment["failure_reason"],
            retry_count=int(payment["retry_count"]),
            recovery_probability=recovery_probability
        )

        # ---------------------------------------------
        # 4. Return complete decision
        # ---------------------------------------------

        return {
            "payment_id": payment["payment_id"],
            "amount": amount,
            "failure_reason": payment["failure_reason"],
            "recovery_probability": round(
                float(recovery_probability),
                4
            ),
            "expected_recovery_value": round(
                expected_recovery_value,
                2
            ),
            "recommended_action": decision.action,
            "decision_status": decision.status,
            "decision_reason": decision.reason,
            "policy_allowed": policy.allowed,
            "policy_status": policy.status,
            "policy_reason": policy.reason,
            "requires_human": policy.requires_human
        }


# ---------------------------------------------------------
# Test one payment
# ---------------------------------------------------------

if __name__ == "__main__":

    workflow = RecoveryWorkflow()

    test_payment = {
        "payment_id": "TEST_001",
        "amount": 2000,
        "payment_method": "UPI",
        "failure_reason": "BANK_TIMEOUT",
        "retry_count": 0,
        "previous_payment_count": 20,
        "previous_success_count": 19,
        "customer_success_rate": 0.95,
        "days_since_last_payment": 7,
        "customer_lifetime_value": 25000
    }

    result = workflow.analyze_payment(
        test_payment
    )

    print("\n")
    print("=" * 60)
    print("             RECOVERAI")
    print("         PAYMENT ANALYSIS")
    print("=" * 60)

    print(
        f"\nPayment ID              : "
        f"{result['payment_id']}"
    )

    print(
        f"Amount                  : "
        f"₹{result['amount']:,.2f}"
    )

    print(
        f"Failure                 : "
        f"{result['failure_reason']}"
    )

    print(
        f"Recovery Probability    : "
        f"{result['recovery_probability']:.2%}"
    )

    print(
        f"Expected Recovery Value : "
        f"₹{result['expected_recovery_value']:,.2f}"
    )

    print(
        f"\nRecommended Action      : "
        f"{result['recommended_action']}"
    )

    print(
        f"Decision Status         : "
        f"{result['decision_status']}"
    )

    print(
        f"Decision Reason         : "
        f"{result['decision_reason']}"
    )

    print(
        f"\nPolicy Allowed          : "
        f"{result['policy_allowed']}"
    )

    print(
        f"Policy Status           : "
        f"{result['policy_status']}"
    )

    print(
        f"Policy Reason           : "
        f"{result['policy_reason']}"
    )

    print(
        f"Human Required          : "
        f"{result['requires_human']}"
    )

    print("\n" + "=" * 60)