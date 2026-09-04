import hashlib
import json
import os

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split

from agent.decision_engine import RecoveryDecisionEngine
from policy.policy_engine import PolicyEngine


# ============================================================
# RecoverAI - Batch Revenue Evaluation
# ============================================================

DATA_PATH = "data/payment_transactions.csv"
MODEL_PATH = "models/recovery_model.pkl"

OUTPUT_PATH = "evaluation/batch_results.csv"
SUMMARY_PATH = "evaluation/batch_summary.json"


# ============================================================
# Model features
# ============================================================

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


# ============================================================
# Synthetic evaluation ground truth
# ============================================================

def calculate_base_probability(row):
    """
    Evaluation-only synthetic probability.

    This reproduces the underlying probability structure
    used when the synthetic dataset was generated.

    IMPORTANT:
    This probability is NOT provided to the ML model.
    It is only used to simulate business outcomes.
    """

    probability = 0.50

    failure_reason = row["failure_reason"]

    if failure_reason == "BANK_TIMEOUT":
        probability += 0.24

    elif failure_reason == "NETWORK_ERROR":
        probability += 0.20

    elif failure_reason == "INSUFFICIENT_FUNDS":
        probability += 0.04

    elif failure_reason == "CARD_EXPIRED":
        probability -= 0.25

    elif failure_reason == "BANK_DECLINED":
        probability -= 0.12

    elif failure_reason == "UNKNOWN_ERROR":
        probability -= 0.15

    # Customer historical behavior
    probability += (
        float(row["customer_success_rate"]) - 0.50
    ) * 0.35

    # Retry pressure
    probability -= (
        int(row["retry_count"]) * 0.10
    )

    # Payment method
    if row["payment_method"] == "UPI":
        probability += 0.03

    elif row["payment_method"] == "CARD":
        probability += 0.01

    # High-value transactions
    if float(row["amount"]) > 25000:
        probability -= 0.10

    return max(
        0.02,
        min(probability, 0.98)
    )


# ============================================================
# Action-specific recovery probability
# ============================================================

def calculate_action_probability(row, action, base_probability):
    """
    Converts the underlying recovery probability into an
    action-specific probability.

    These are synthetic evaluation assumptions.

    They are NOT Razorpay production conversion rates.

    The purpose is to model the fact that different recovery
    interventions behave differently.
    """

    failure_reason = row["failure_reason"]

    # --------------------------------------------------------
    # RETRY
    # --------------------------------------------------------

    if action == "RETRY":

        # Retry is most appropriate for temporary failures.
        if failure_reason in {
            "BANK_TIMEOUT",
            "NETWORK_ERROR"
        }:

            # Repeated attempts become less effective.
            retry_count = int(row["retry_count"])

            probability = (
                base_probability
                * (1 - 0.08 * retry_count)
            )

            return max(
                0.01,
                min(probability, 0.98)
            )

        # Retry should not normally be used for permanent /
        # customer-action failures.
        return 0.0

    # --------------------------------------------------------
    # PAYMENT REMINDER
    # --------------------------------------------------------

    if action == "PAYMENT_REMINDER":

        if failure_reason == "INSUFFICIENT_FUNDS":

            # Reminder allows the customer to resolve the
            # balance before trying again.
            probability = base_probability * 1.10

        elif failure_reason == "BANK_DECLINED":

            probability = base_probability * 0.95

        elif failure_reason in {
            "BANK_TIMEOUT",
            "NETWORK_ERROR"
        }:

            # Slightly less direct than retry.
            probability = base_probability * 0.90

        elif failure_reason == "UNKNOWN_ERROR":

            probability = base_probability * 0.95

        else:

            probability = base_probability * 0.85

        return max(
            0.01,
            min(probability, 0.98)
        )

    # --------------------------------------------------------
    # UPDATE PAYMENT METHOD
    # --------------------------------------------------------

    if action == "UPDATE_PAYMENT_METHOD":

        if failure_reason == "CARD_EXPIRED":

            # Updating an expired payment method addresses the
            # actual cause of failure.
            probability = (
                base_probability + 0.50
            )

            return max(
                0.01,
                min(probability, 0.95)
            )

        return 0.0

    # --------------------------------------------------------
    # HUMAN REVIEW
    # --------------------------------------------------------

    if action == "HUMAN_REVIEW":

        # Human review is an escalation, not an automatic
        # revenue recovery action in this simulation.
        return 0.0

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    if action == "STOP":
        return 0.0

    return 0.0


# ============================================================
# Deterministic random number
# ============================================================

def deterministic_random(payment_id):
    """
    Generates the same random number for the same payment.

    This keeps the evaluation reproducible.
    """

    digest = hashlib.sha256(
        payment_id.encode()
    ).hexdigest()

    integer = int(
        digest[:8],
        16
    )

    return integer / 0xFFFFFFFF


# ============================================================
# Simulate action success
# ============================================================

def simulate_success(
    payment_id,
    action_probability
):
    """
    Simulates whether an intervention succeeds.

    The same payment receives the same underlying random
    number, making repeated evaluation runs reproducible.
    """

    random_value = deterministic_random(
        payment_id
    )

    return random_value < action_probability


# ============================================================
# Baseline strategy
# ============================================================

def baseline_action(row):
    """
    Simple non-ML baseline.

    The baseline retries temporary failures when the retry
    limit has not been reached.
    """

    temporary_failures = {
        "BANK_TIMEOUT",
        "NETWORK_ERROR"
    }

    if (
        row["failure_reason"]
        in temporary_failures
        and int(row["retry_count"]) < 2
    ):
        return "RETRY"

    return "NO_ACTION"


# ============================================================
# Main evaluation
# ============================================================

def main():

    print("=" * 75)
    print("             RecoverAI - Batch Evaluation")
    print("=" * 75)

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    df = pd.read_csv(
        DATA_PATH
    )

    print(
        f"\nTotal dataset: {len(df):,}"
    )

    # --------------------------------------------------------
    # Recreate unseen test split
    # --------------------------------------------------------

    X = df[FEATURES]

    y = df["recovered"]

    _, X_test, _, _ = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    test_ids = X_test.index

    test_df = (
        df.loc[test_ids]
        .copy()
        .reset_index(drop=True)
    )

    print(
        f"Unseen evaluation batch: "
        f"{len(test_df):,}"
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print("\nLoading recovery model...")

    model = joblib.load(
        MODEL_PATH
    )

    print("Recovery model loaded.")

    # --------------------------------------------------------
    # Initialize engines
    # --------------------------------------------------------

    decision_engine = (
        RecoveryDecisionEngine()
    )

    policy_engine = (
        PolicyEngine()
    )

    # --------------------------------------------------------
    # Batch ML prediction
    # --------------------------------------------------------

    print(
        "\nRunning ML predictions..."
    )

    ml_probabilities = (
        model.predict_proba(
            test_df[FEATURES]
        )[:, 1]
    )

    print(
        "ML predictions completed."
    )

    # --------------------------------------------------------
    # Process payments
    # --------------------------------------------------------

    results = []

    total_rows = len(test_df)

    print(
        f"\nProcessing "
        f"{total_rows:,} evaluation payments..."
    )

    for position, (_, row) in enumerate(
        test_df.iterrows()
    ):

        payment_id = row["payment_id"]

        amount = float(
            row["amount"]
        )

        failure_reason = (
            row["failure_reason"]
        )

        retry_count = int(
            row["retry_count"]
        )

        # ----------------------------------------------------
        # ML prediction
        # ----------------------------------------------------

        recovery_probability = float(
            ml_probabilities[position]
        )

        expected_value = (
            amount *
            recovery_probability
        )

        # ----------------------------------------------------
        # RecoverAI decision
        # ----------------------------------------------------

        decision = decision_engine.decide(
            amount=amount,
            failure_reason=failure_reason,
            retry_count=retry_count,
            recovery_probability=recovery_probability
        )

        # ----------------------------------------------------
        # Policy validation
        # ----------------------------------------------------

        policy = policy_engine.check(
            action=decision.action,
            amount=amount,
            failure_reason=failure_reason,
            retry_count=retry_count,
            recovery_probability=recovery_probability
        )

        # ----------------------------------------------------
        # Synthetic underlying probability
        # ----------------------------------------------------

        base_probability = (
            calculate_base_probability(row)
        )

        # ----------------------------------------------------
        # RecoverAI action probability
        # ----------------------------------------------------

        recoverai_action_probability = (
            calculate_action_probability(
                row,
                decision.action,
                base_probability
            )
        )

        # ----------------------------------------------------
        # RecoverAI execution
        # ----------------------------------------------------

        recoverai_success = False

        if policy.allowed:

            if decision.action in {
                "RETRY",
                "PAYMENT_REMINDER",
                "UPDATE_PAYMENT_METHOD"
            }:

                recoverai_success = (
                    simulate_success(
                        payment_id,
                        recoverai_action_probability
                    )
                )

        recoverai_recovered_amount = (
            amount
            if recoverai_success
            else 0.0
        )

        # ----------------------------------------------------
        # Baseline
        # ----------------------------------------------------

        baseline = baseline_action(
            row
        )

        baseline_success = False

        baseline_probability = 0.0

        if baseline == "RETRY":

            baseline_probability = (
                calculate_action_probability(
                    row,
                    "RETRY",
                    base_probability
                )
            )

            baseline_success = (
                simulate_success(
                    payment_id,
                    baseline_probability
                )
            )

        baseline_recovered_amount = (
            amount
            if baseline_success
            else 0.0
        )

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        results.append({

            "payment_id":
                payment_id,

            "amount":
                amount,

            "failure_reason":
                failure_reason,

            "payment_method":
                row["payment_method"],

            "retry_count":
                retry_count,

            "customer_success_rate":
                row["customer_success_rate"],

            "ml_recovery_probability":
                round(
                    recovery_probability,
                    4
                ),

            "expected_recovery_value":
                round(
                    expected_value,
                    2
                ),

            "base_simulation_probability":
                round(
                    base_probability,
                    4
                ),

            "recommended_action":
                decision.action,

            "decision_status":
                decision.status,

            "decision_reason":
                decision.reason,

            "policy_allowed":
                policy.allowed,

            "policy_status":
                policy.status,

            "policy_reason":
                policy.reason,

            "requires_human":
                policy.requires_human,

            "recoverai_action_probability":
                round(
                    recoverai_action_probability,
                    4
                ),

            "baseline_action":
                baseline,

            "baseline_probability":
                round(
                    baseline_probability,
                    4
                ),

            "baseline_success":
                int(
                    baseline_success
                ),

            "baseline_recovered_amount":
                round(
                    baseline_recovered_amount,
                    2
                ),

            "recoverai_success":
                int(
                    recoverai_success
                ),

            "recoverai_recovered_amount":
                round(
                    recoverai_recovered_amount,
                    2
                )
        })

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if (
            position + 1
        ) % 500 == 0:

            print(
                f"Processed "
                f"{position + 1:,}/"
                f"{total_rows:,}"
            )

    # ========================================================
    # Results DataFrame
    # ========================================================

    results_df = pd.DataFrame(
        results
    )

    # ========================================================
    # Overall metrics
    # ========================================================

    total_at_risk = (
        results_df[
            "amount"
        ].sum()
    )

    baseline_recovered = (
        results_df[
            "baseline_recovered_amount"
        ].sum()
    )

    recoverai_recovered = (
        results_df[
            "recoverai_recovered_amount"
        ].sum()
    )

    baseline_successes = (
        results_df[
            "baseline_success"
        ].sum()
    )

    recoverai_successes = (
        results_df[
            "recoverai_success"
        ].sum()
    )

    allowed_actions = (
        results_df[
            "policy_allowed"
        ].sum()
    )

    human_escalations = (
        results_df[
            "requires_human"
        ].sum()
    )

    blocked_actions = (
        results_df[
            "policy_status"
        ]
        .eq("BLOCKED")
        .sum()
    )

    stopped_actions = (
        results_df[
            "policy_status"
        ]
        .eq("STOPPED")
        .sum()
    )

    # ========================================================
    # Recovery rates
    # ========================================================

    baseline_rate = (
        baseline_recovered /
        total_at_risk
        if total_at_risk > 0
        else 0
    )

    recoverai_rate = (
        recoverai_recovered /
        total_at_risk
        if total_at_risk > 0
        else 0
    )

    # ========================================================
    # Incremental revenue
    # ========================================================

    incremental_revenue = (
        recoverai_recovered -
        baseline_recovered
    )

    # ========================================================
    # Action-level metrics
    # ========================================================

    action_metrics = {}

    for action in sorted(
        results_df[
            "recommended_action"
        ].unique()
    ):

        action_df = results_df[
            results_df[
                "recommended_action"
            ] == action
        ]

        action_metrics[action] = {

            "payments": int(
                len(action_df)
            ),

            "successful_recoveries": int(
                action_df[
                    "recoverai_success"
                ].sum()
            ),

            "revenue_recovered": round(
                float(
                    action_df[
                        "recoverai_recovered_amount"
                    ].sum()
                ),
                2
            ),

            "recovery_rate": round(
                float(
                    action_df[
                        "recoverai_recovered_amount"
                    ].sum()
                )
                /
                float(
                    action_df[
                        "amount"
                    ].sum()
                )
                if action_df[
                    "amount"
                ].sum() > 0
                else 0,
                4
            )
        }

    # ========================================================
    # Failure-level metrics
    # ========================================================

    failure_metrics = {}

    for failure in sorted(
        results_df[
            "failure_reason"
        ].unique()
    ):

        failure_df = results_df[
            results_df[
                "failure_reason"
            ] == failure
        ]

        failure_metrics[failure] = {

            "payments": int(
                len(failure_df)
            ),

            "revenue_at_risk": round(
                float(
                    failure_df[
                        "amount"
                    ].sum()
                ),
                2
            ),

            "recoverai_revenue": round(
                float(
                    failure_df[
                        "recoverai_recovered_amount"
                    ].sum()
                ),
                2
            ),

            "successful_recoveries": int(
                failure_df[
                    "recoverai_success"
                ].sum()
            )
        }

    # ========================================================
    # Save detailed results
    # ========================================================

    os.makedirs(
        "evaluation",
        exist_ok=True
    )

    results_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    # ========================================================
    # Summary JSON
    # ========================================================

    summary = {

        "evaluation_type":
            "synthetic_action_aware_simulation",

        "evaluation_batch_size":
            int(len(results_df)),

        "total_revenue_at_risk":
            round(
                float(total_at_risk),
                2
            ),

        "baseline_recovered_revenue":
            round(
                float(baseline_recovered),
                2
            ),

        "recoverai_recovered_revenue":
            round(
                float(recoverai_recovered),
                2
            ),

        "incremental_revenue_vs_baseline":
            round(
                float(incremental_revenue),
                2
            ),

        "baseline_successful_recoveries":
            int(baseline_successes),

        "recoverai_successful_recoveries":
            int(recoverai_successes),

        "baseline_recovery_rate":
            round(
                float(baseline_rate),
                4
            ),

        "recoverai_recovery_rate":
            round(
                float(recoverai_rate),
                4
            ),

        "recoverai_allowed_actions":
            int(allowed_actions),

        "human_escalations":
            int(human_escalations),

        "blocked_actions":
            int(blocked_actions),

        "stopped_actions":
            int(stopped_actions),

        "action_metrics":
            action_metrics,

        "failure_metrics":
            failure_metrics
    }

    with open(
        SUMMARY_PATH,
        "w"
    ) as file:

        json.dump(
            summary,
            file,
            indent=4
        )

    # ========================================================
    # Final output
    # ========================================================

    print("\n")
    print("=" * 75)
    print("                    FINAL RESULTS")
    print("=" * 75)

    print(
        f"\nEvaluation batch:"
        f" {len(results_df):,} payments"
    )

    print(
        f"\nRevenue at risk:"
        f" ₹{total_at_risk:,.2f}"
    )

    # ========================================================
    # BASELINE
    # ========================================================

    print("\nBASELINE")
    print("-" * 50)

    print(
        f"Successful recoveries:"
        f" {baseline_successes:,}"
    )

    print(
        f"Revenue recovered:"
        f" ₹{baseline_recovered:,.2f}"
    )

    print(
        f"Recovery rate:"
        f" {baseline_rate:.2%}"
    )

    # ========================================================
    # RECOVERAI
    # ========================================================

    print("\nRECOVERAI")
    print("-" * 50)

    print(
        f"Successful recoveries:"
        f" {recoverai_successes:,}"
    )

    print(
        f"Revenue recovered:"
        f" ₹{recoverai_recovered:,.2f}"
    )

    print(
        f"Recovery rate:"
        f" {recoverai_rate:.2%}"
    )

    print(
        f"Allowed actions:"
        f" {allowed_actions:,}"
    )

    print(
        f"Human escalations:"
        f" {human_escalations:,}"
    )

    print(
        f"Blocked actions:"
        f" {blocked_actions:,}"
    )

    print(
        f"Stopped actions:"
        f" {stopped_actions:,}"
    )

    # ========================================================
    # ACTION BREAKDOWN
    # ========================================================

    print("\nACTION BREAKDOWN")
    print("-" * 50)

    for action, metrics in action_metrics.items():

        print(
            f"\n{action}"
        )

        print(
            f"  Payments:"
            f" {metrics['payments']:,}"
        )

        print(
            f"  Recoveries:"
            f" {metrics['successful_recoveries']:,}"
        )

        print(
            f"  Revenue:"
            f" ₹{metrics['revenue_recovered']:,.2f}"
        )

        print(
            f"  Recovery rate:"
            f" {metrics['recovery_rate']:.2%}"
        )

    # ========================================================
    # BUSINESS IMPACT
    # ========================================================

    print("\nBUSINESS IMPACT")
    print("-" * 50)

    print(
        f"Incremental revenue vs baseline:"
        f" ₹{incremental_revenue:,.2f}"
    )

    if incremental_revenue > 0:

        print(
            "\nSUCCESS:"
            " RecoverAI generated positive"
            " incremental revenue."
        )

    elif incremental_revenue < 0:

        print(
            "\nNOTE:"
            " RecoverAI is currently below"
            " the baseline in this simulation."
        )

    else:

        print(
            "\nNOTE:"
            " RecoverAI matched the baseline."
        )

    # ========================================================
    # Output files
    # ========================================================

    print("\n")
    print(
        f"Detailed results saved to:"
        f" {OUTPUT_PATH}"
    )

    print(
        f"Summary saved to:"
        f" {SUMMARY_PATH}"
    )

    print("=" * 75)


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()