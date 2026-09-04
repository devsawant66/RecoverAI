import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ============================================================
# RecoverAI - Synthetic Payment Dataset Generator
# ============================================================

SEED = 42
NUM_RECORDS = 20000

random.seed(SEED)
np.random.seed(SEED)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

PAYMENT_METHODS = [
    "UPI",
    "CARD",
    "NETBANKING",
    "WALLET"
]

FAILURE_REASONS = [
    "BANK_TIMEOUT",
    "NETWORK_ERROR",
    "INSUFFICIENT_FUNDS",
    "CARD_EXPIRED",
    "BANK_DECLINED",
    "UNKNOWN_ERROR"
]

FAILURE_WEIGHTS = [
    0.25,
    0.20,
    0.20,
    0.10,
    0.20,
    0.05
]

MERCHANTS = [
    "DEV_CLOTHING_STORE"
]


# ------------------------------------------------------------
# Customer generation
# ------------------------------------------------------------

def generate_customer_profile():
    """
    Generate realistic customer payment history.
    """

    previous_payments = random.randint(1, 50)

    # Historical payment success rate
    historical_success_rate = np.random.beta(8, 2)

    previous_successes = round(
        previous_payments * historical_success_rate
    )

    previous_successes = min(
        previous_successes,
        previous_payments
    )

    actual_success_rate = (
        previous_successes / previous_payments
    )

    days_since_last_payment = random.randint(1, 180)

    customer_lifetime_value = round(
        np.random.lognormal(
            mean=8.2,
            sigma=0.9
        ),
        2
    )

    return {
        "previous_payment_count": previous_payments,
        "previous_success_count": previous_successes,
        "customer_success_rate": round(
            actual_success_rate,
            3
        ),
        "days_since_last_payment": days_since_last_payment,
        "customer_lifetime_value": customer_lifetime_value
    }


# ------------------------------------------------------------
# Payment amount generation
# ------------------------------------------------------------

def generate_payment_amount():
    """
    Generate realistic clothing-store purchase amounts.

    Most orders are normal purchases.
    Larger orders are less common.
    """

    amount = random.choices(
        [
            random.uniform(300, 1500),      # Normal order
            random.uniform(1500, 3000),     # Medium order
            random.uniform(3000, 8000),     # Large order
            random.uniform(8000, 20000)     # Rare high-value order
        ],
        weights=[
            0.45,
            0.35,
            0.15,
            0.05
        ],
        k=1
    )[0]

    return round(amount, 2)

# ------------------------------------------------------------
# Failure reason generation
# ------------------------------------------------------------

def generate_failure_reason():
    return random.choices(
        FAILURE_REASONS,
        weights=FAILURE_WEIGHTS,
        k=1
    )[0]


# ------------------------------------------------------------
# Latent recovery probability
# ------------------------------------------------------------

def calculate_true_recovery_probability(
    failure_reason,
    customer_success_rate,
    retry_count,
    payment_method,
    amount
):
    """
    Creates the hidden probability used only for
    synthetic outcome generation.

    IMPORTANT:
    This value will NOT be given to the ML model.

    It represents the underlying probability that
    a failed payment could eventually be recovered.
    """

    probability = 0.50

    # Failure characteristics
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
        customer_success_rate - 0.5
    ) * 0.35

    # Repeated retries reduce likelihood
    probability -= retry_count * 0.10

    # Payment method effects
    if payment_method == "UPI":
        probability += 0.03

    elif payment_method == "CARD":
        probability += 0.01

    # Large payments require more caution
    if amount > 25000:
        probability -= 0.10

    return np.clip(
        probability,
        0.02,
        0.98
    )


# ------------------------------------------------------------
# Generate actual recovery outcome
# ------------------------------------------------------------

def generate_recovery_outcome(true_probability):
    """
    Generate the actual outcome independently from
    the probability.

    1 = eventually recovered
    0 = not recovered
    """

    return int(
        random.random() < true_probability
    )

def generate_customers(num_customers=5000):
    """
    Generate persistent customer profiles.

    Each customer keeps the same historical
    behavior across multiple transactions.
    """

    customers = {}

    for i in range(1, num_customers + 1):

        customer_id = f"CUST_{i:05d}"

        previous_payments = random.randint(2, 50)

        historical_success_rate = np.random.beta(
            8,
            2
        )

        previous_successes = round(
            previous_payments *
            historical_success_rate
        )

        previous_successes = min(
            previous_successes,
            previous_payments
        )

        customers[customer_id] = {
            "previous_payment_count":
                previous_payments,

            "previous_success_count":
                previous_successes,

            "customer_success_rate":
                round(
                    previous_successes /
                    previous_payments,
                    3
                ),

            "days_since_last_payment":
                random.randint(1, 180),

            "customer_lifetime_value":
                round(
                    np.random.lognormal(
                        mean=8.2,
                        sigma=0.9
                    ),
                    2
                )
        }

    return customers






# ------------------------------------------------------------
# Generate transactions
# ------------------------------------------------------------

def generate_dataset():

    records = []

    start_date = datetime.now() - timedelta(
    days=180
)

    customers = generate_customers(
    num_customers=5000
)

    for i in range(NUM_RECORDS):

        payment_id = f"PAY_{i + 1:07d}"

        customer_id = random.choice(
        list(customers.keys())
)
        

        merchant_id = random.choice(
            MERCHANTS
        )

        amount = generate_payment_amount()

        payment_method = random.choice(
            PAYMENT_METHODS
        )

        transaction_time = (
            start_date
            + timedelta(
                minutes=random.randint(
                    0,
                    180 * 24 * 60
                )
            )
        )

        customer = customers[customer_id].copy()

        failure_reason = generate_failure_reason()

        retry_count = random.randint(0, 2)

        # Hidden probability used only to generate
        # the synthetic ground truth.
        true_probability = (
            calculate_true_recovery_probability(
                failure_reason=failure_reason,
                customer_success_rate=
                    customer["customer_success_rate"],
                retry_count=retry_count,
                payment_method=payment_method,
                amount=amount
            )
        )

        recovered = generate_recovery_outcome(
            true_probability
        )

        recovered_amount = (
            amount if recovered == 1 else 0
        )

        record = {

            # -------------------------------
            # Transaction information
            # -------------------------------

            "payment_id": payment_id,

            "customer_id": customer_id,

            "merchant_id": merchant_id,

            "amount": amount,

            "payment_method": payment_method,

            "transaction_time":
                transaction_time,

            # -------------------------------
            # Failure information
            # -------------------------------

            "payment_status": "FAILED",

            "failure_reason":
                failure_reason,

            "retry_count":
                retry_count,

            # -------------------------------
            # Customer behavior
            # -------------------------------

            "previous_payment_count":
                customer[
                    "previous_payment_count"
                ],

            "previous_success_count":
                customer[
                    "previous_success_count"
                ],

            "customer_success_rate":
                customer[
                    "customer_success_rate"
                ],

            "days_since_last_payment":
                customer[
                    "days_since_last_payment"
                ],

            "customer_lifetime_value":
                customer[
                    "customer_lifetime_value"
                ],

            # -------------------------------
            # Ground truth
            # -------------------------------

            "recovered":
                recovered,

            "recovered_amount":
                round(
                    recovered_amount,
                    2
                )
        }

        records.append(record)

    df = pd.DataFrame(records)

    return df


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 65)
    print("        RecoverAI - Dataset Generator")
    print("=" * 65)

    df = generate_dataset()

    output_file = (
        "data/payment_transactions.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    total_failed_revenue = (
        df["amount"].sum()
    )

    recovered_revenue = (
        df["recovered_amount"].sum()
    )

    recovery_rate = (
        df["recovered"].mean() * 100
    )

    print(
        f"\nTransactions generated : "
        f"{len(df):,}"
    )

    print(
        f"Total failed revenue   : "
        f"₹{total_failed_revenue:,.2f}"
    )

    print(
        f"Recovered revenue      : "
        f"₹{recovered_revenue:,.2f}"
    )

    print(
        f"Recovery rate          : "
        f"{recovery_rate:.2f}%"
    )

    print("\nFailure distribution:")
    print(
        df["failure_reason"]
        .value_counts()
        .to_string()
    )

    print("\nPayment methods:")
    print(
        df["payment_method"]
        .value_counts()
        .to_string()
    )

    print("\nSample records:")
    print(
        df.head(5).to_string()
    )

    print(
        f"\nDataset saved to: "
        f"{output_file}"
    )

    print("=" * 65)