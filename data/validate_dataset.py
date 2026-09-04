import pandas as pd


DATA_PATH = "data/payment_transactions.csv"


def main():

    print("=" * 70)
    print("RecoverAI - Dataset Validation")
    print("=" * 70)

    df = pd.read_csv(DATA_PATH)

    print("\n1. Dataset shape")
    print(df.shape)

    print("\n2. Columns")
    for column in df.columns:
        print(" -", column)

    print("\n3. Missing values")
    missing = df.isnull().sum()

    print(missing)

    print("\n4. Duplicate payment IDs")

    duplicates = df["payment_id"].duplicated().sum()

    print(
        f"Duplicate payment IDs: {duplicates}"
    )

    print("\n5. Payment status distribution")

    print(
        df["payment_status"]
        .value_counts()
    )

    print("\n6. Failure reason distribution")

    print(
        df["failure_reason"]
        .value_counts()
    )

    print("\n7. Payment method distribution")

    print(
        df["payment_method"]
        .value_counts()
    )

    print("\n8. Recovery distribution")

    print(
        df["recovered"]
        .value_counts()
    )

    print("\n9. Recovery percentage")

    recovery_rate = (
        df["recovered"].mean() * 100
    )

    print(
        f"{recovery_rate:.2f}%"
    )

    print("\n10. Revenue")

    total_revenue = df["amount"].sum()

    recovered_revenue = (
        df["recovered_amount"].sum()
    )

    print(
        f"Failed revenue: ₹{total_revenue:,.2f}"
    )

    print(
        f"Recovered revenue: "
        f"₹{recovered_revenue:,.2f}"
    )

    print("\n11. Basic statistics")

    print(
        df[
            [
                "amount",
                "retry_count",
                "customer_success_rate",
                "customer_lifetime_value"
            ]
        ].describe()
    )

    print("\n" + "=" * 70)
    print("Validation completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()