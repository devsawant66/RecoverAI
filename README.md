# RECOVERAI

### AI-Powered Revenue Recovery for Failed Payments

> **Predict. Decide. Recover. Stop Safely.**

RECOVERAI is an AI-powered revenue recovery decision system designed to help merchants intelligently respond to failed payments.

Instead of blindly retrying every failed transaction, RECOVERAI evaluates payment context, estimates recovery probability, selects the most appropriate intervention, applies deterministic safety policies, and records the complete decision trail.

---

## 🚀 The Problem

A failed payment is not always a lost customer.

For a merchant, every failed transaction represents **revenue at risk**.

Traditional recovery systems often rely on simple retry rules:

```text
Payment Failed
      ↓
Retry
      ↓
Retry Again







 Our Solution

RECOVERAI combines:

Machine Learning + Decision Intelligence + Policy Controls + Human Escalation + Auditability

                 FAILED PAYMENT
                       │
                       ▼
              Transaction Context
                       │
                       ▼
             ┌───────────────────┐
             │   ML Prediction   │
             │ Recovery Probability│
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │  Decision Engine  │
             │ What should we do?│
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │   Policy Engine   │
             │ Is it safe/allowed?│
             └─────────┬─────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
        ACTION       HUMAN         STOP
          │          REVIEW          │
          ▼            │             │
       Recovery        │             │
          │            │             │
          └────────────┼─────────────┘
                       ▼
                 Outcome + Audit
                       │
                       ▼
                ₹ Revenue Impact
🧠 How RECOVERAI Works
1. Payment Failure Detection

RECOVERAI starts with failed payment transactions containing information such as:

Payment amount
Payment method
Failure reason
Retry count
Previous payment history
Customer success rate
Days since previous payment
Customer lifetime value

The current synthetic dataset contains:

20,000 failed payment transactions.

2. AI Recovery Prediction

A Random Forest classification model estimates the probability that a failed payment can be recovered.

Model features
amount
payment_method
failure_reason
retry_count
previous_payment_count
previous_success_count
customer_success_rate
days_since_last_payment
customer_lifetime_value

The model intentionally excludes outcome variables such as:

recovered
recovered_amount

to avoid target leakage.

📊 Machine Learning Performance
Metric	Result
Accuracy	67.65%
Precision	71.88%
Recall	70.55%
F1 Score	71.21%
ROC-AUC	72.42%

These are ML classification metrics. They are different from the business recovery rate reported below.

🤖 3. Recovery Decision Engine

The ML model predicts probability, but it does not directly authorize an action.

The Decision Engine combines the prediction with payment context.

Available actions
Action	Purpose
RETRY	Reattempt suitable temporary failures
PAYMENT_REMINDER	Encourage the customer to complete payment
UPDATE_PAYMENT_METHOD	Handle issues such as expired cards
HUMAN_REVIEW	Escalate uncertain or sensitive cases
STOP	Stop when further recovery is not justified

RECOVERAI also calculates:

Expected Recovery Value
=
Payment Amount × Recovery Probability

Example:

Payment Amount = ₹5,000
Recovery Probability = 80%

Expected Recovery Value = ₹4,000
🛡️ 4. Policy & Safety Engine

Prediction does not automatically mean permission.

RECOVERAI uses a separate deterministic Policy Engine to validate the proposed action.

Safety controls
Maximum automatic retries: 2
Automatic retry probability threshold: 70%
High-value protection threshold: ₹10,000
Automatic retries restricted to temporary failures
Low-confidence actions can be escalated
Human review supported
Explicit STOP decisions
Audit logging

This creates a separation between:

AI Prediction
      ↓
Recommended Action
      ↓
Policy Validation
      ↓
Allowed / Escalated / Blocked / Stopped
💰 5. Revenue Recovery Evaluation

RECOVERAI was evaluated using a 4,000-payment synthetic action-aware evaluation batch.

Business Impact
Metric	Baseline	RECOVERAI
Recovery Rate	22.83%	31.83%
Successful Recoveries	939	1,455
Revenue Recovered	₹25.82 L	₹36.01 L
Incremental Revenue

₹10.18 lakh

RECOVERAI generated approximately:

₹10.18 lakh more simulated recovered revenue than the baseline strategy.

Evaluation revenue at risk

₹1.13 crore

📈 Evaluation Summary
Evaluation payments        4,000
Revenue at risk            ₹1.13 Cr
Baseline recovered         ₹25.82 L
RECOVERAI recovered        ₹36.01 L
Incremental recovery       ₹10.18 L
Baseline recovery rate     22.83%
RECOVERAI recovery rate    31.83%
Successful recoveries      1,455
Human escalations          725
Stopped actions            1,302
Blocked actions            0

Important: These results come from a synthetic action-aware evaluation and do not represent real production Razorpay transactions or real recovered money.

🔍 Recovery Actions

RECOVERAI does not apply one recovery strategy to every failure.

Examples:

BANK_TIMEOUT

Potentially temporary:

High recovery probability
        ↓
RETRY
NETWORK_ERROR

Potentially temporary:

High confidence
        ↓
RETRY
INSUFFICIENT_FUNDS
Payment may succeed later
        ↓
PAYMENT_REMINDER
CARD_EXPIRED
Retrying the same card is ineffective
        ↓
UPDATE_PAYMENT_METHOD
High-value / uncertain cases
Risk-sensitive case
        ↓
HUMAN_REVIEW
Low-confidence / exhausted retries
Further recovery not justified
        ↓
STOP
👤 Human-in-the-Loop

RECOVERAI does not attempt to automate every financial decision.

Cases that are uncertain or sensitive can be routed to human review.

Current evaluation:

725 human escalations

This provides a controlled balance between automation and human oversight.

📋 Auditability

Every recovery workflow can be represented as a traceable decision:

Payment
   ↓
Transaction Context
   ↓
Recovery Probability
   ↓
Recommended Action
   ↓
Policy Decision
   ↓
Execution Status
   ↓
Recovery Outcome

The audit layer records information such as:

Timestamp
Payment ID
Customer ID
Merchant ID
Amount
Failure reason
Recovery probability
Expected recovery value
Recommended action
Policy status
Execution status
Recovery result
Recovered amount
📊 RECOVERAI Command Center

The project includes a Streamlit dashboard with:

Overview

Business-level recovery KPIs and revenue impact.

Revenue Recovery

Recovery performance by intervention.

AI Decision Center

AI decisions, model performance, and recovery policy.

Failure Intelligence

Revenue-at-risk and recovery analysis by failure reason.

Payment Explorer

Transaction-level inspection and filtering.

Safety & Governance

Retry limits, confidence thresholds, escalation and stopping controls.

Audit Trail

Traceable recovery decisions and evaluation outcomes.

🏗️ Project Structure
RecoverAI/
│
├── agent/
│   ├── __init__.py
│   ├── decision_engine.py
│   ├── explanation.py
│   └── recovery_workflow.py
│
├── api/
│   ├── __init__.py
│   ├── audit.py
│   └── main.py
│
├── dashboard/
│   └── app.py
│
├── data/
│   └── generate_dataset.py
│
├── evaluation/
│   ├── run_batch.py
│   ├── batch_results.csv
│   └── batch_summary.json
│
├── models/
│   ├── __init__.py
│   ├── model_metrics.json
│   ├── predict_model.py
│   └── train_recovery_model.py
│
├── policy/
│   ├── __init__.py
│   └── policy_engine.py
│
├── tests/
│
├── .gitignore
├── README.md
└── requirements.txt
⚙️ Tech Stack
AI / Machine Learning
Python
Scikit-learn
Random Forest
Pandas
NumPy
Backend
FastAPI
Python
Dashboard
Streamlit
Plotly
Data & Evaluation
CSV
JSON
Synthetic payment transaction data
Action-aware recovery simulation
▶️ Run Locally
1. Clone the repository
git clone https://github.com/devsawant66/RecoverAI.git
cd RecoverAI
2. Create a virtual environment
python -m venv venv

Activate it on Windows:

venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
4. Run the dashboard
streamlit run dashboard/app.py

The RECOVERAI Command Center will open in your browser.

🧪 Run the Evaluation

To reproduce the synthetic action-aware evaluation:

python evaluation/run_batch.py

This generates evaluation outputs including:

evaluation/batch_results.csv
evaluation/batch_summary.json
🔐 Security

Sensitive credentials must never be committed to the repository.

The project intentionally excludes:

.env
venv/
__pycache__/
*.pyc
models/recovery_model.pkl
api/audit_log.json

The trained model artifact and runtime audit log are generated locally rather than committed to the public repository.

⚠️ Disclaimer

RECOVERAI is a hackathon/prototype project.

The payment dataset and revenue-recovery results are synthetic and used for demonstration and evaluation.

The reported:

₹10.18 lakh incremental revenue

is a simulated action-aware evaluation result and does not represent real money recovered from Razorpay production transactions.

🎯 Vision

RECOVERAI aims to move payment recovery from:

"Retry failed payments."

to:

"Understand the failure, estimate the opportunity, choose the right intervention, act within policy, and measure the revenue recovered."

RECOVERAI

Predict. Decide. Recover. Stop Safely.


### After pasting

Click:

**Commit changes**

Use this commit message:

```text
Improve RECOVERAI project documentation

Then commit.

After that, send me a screenshot of the top of your GitHub repository. We'll add your dashboard screenshots next, which will make the repository look much more impressive to judges/recruiters.
