import joblib
import pandas as pd


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


def predict_payment(payment_data: dict):

    model = joblib.load(MODEL_PATH)

    payment_df = pd.DataFrame(
        [payment_data]
    )

    probability = model.predict_proba(
        payment_df[FEATURES]
    )[0][1]

    amount = float(
        payment_data["amount"]
    )

    expected_recovery_value = (
        amount * probability
    )

    return {
        "recovery_probability":
            round(float(probability), 4),

        "expected_recovery_value":
            round(
                expected_recovery_value,
                2
            )
    }

def predict_recovery_probability(row):
    """
    Predict recovery probability for a single payment row.
    """

    import pandas as pd
    import joblib
    import os

    model_path = os.path.join(
        os.path.dirname(__file__),
        "recovery_model.pkl"
    )

    model = joblib.load(model_path)

    features = [
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

    input_data = pd.DataFrame(
        [{
            feature: row[feature]
            for feature in features
        }]
    )

    probability = model.predict_proba(
        input_data
    )[0][1]

    return float(probability)
if __name__ == "__main__":

    example_payment = {
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

    result = predict_payment(
        example_payment
    )

    print("\nRecoverAI Prediction")
    print("=" * 40)

    print(
        f"Recovery probability: "
        f"{result['recovery_probability']:.2%}"
    )

    print(
        f"Expected recovery value: "
        f"₹{result['expected_recovery_value']:,.2f}"
    )
    