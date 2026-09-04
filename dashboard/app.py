import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# RECOVERAI — AI REVENUE RECOVERY COMMAND CENTER
# ============================================================

st.set_page_config(
    page_title="RecoverAI | Revenue Recovery",
    page_icon="↗",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_FILE = ROOT / "evaluation" / "batch_summary.json"
RESULTS_FILE = ROOT / "evaluation" / "batch_results.csv"
PAYMENTS_FILE = ROOT / "data" / "payment_transactions.csv"
AUDIT_FILE = ROOT / "api" / "audit_log.json"

# ---------- Theme ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background: #f6f8fb;
}
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2.5rem;
    max-width: 1500px;
}
[data-testid="stSidebar"] {
    background: #0b1220;
}
[data-testid="stSidebar"] * {
    color: #e8edf5 !important;
}
.brand {
    padding: 8px 4px 22px 4px;
}
.brand-title {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -1px;
}
.brand-title span {
    color: #42d392;
}
.brand-sub {
    color: #9aa8bd !important;
    font-size: 12px;
    margin-top: 4px;
}
.hero {
    background: linear-gradient(135deg,#0b1220 0%,#16233b 65%,#173b3a 100%);
    border-radius: 18px;
    padding: 28px 32px;
    color: white;
    margin-bottom: 22px;
    box-shadow: 0 10px 35px rgba(11,18,32,.12);
}
.hero h1 {
    margin: 0;
    font-size: 34px;
    letter-spacing: -1.2px;
}
.hero p {
    color: #c8d2df;
    margin: 8px 0 0;
    font-size: 14px;
}
.kpi {
    background: white;
    border: 1px solid #e6eaf0;
    border-radius: 15px;
    padding: 18px 20px;
    min-height: 112px;
    box-shadow: 0 3px 12px rgba(15,23,42,.04);
}
.kpi-label {
    color: #667085;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .5px;
}
.kpi-value {
    color: #101828;
    font-size: 27px;
    font-weight: 800;
    margin-top: 7px;
}
.kpi-note {
    color: #12a66a;
    font-size: 11px;
    margin-top: 5px;
    font-weight: 600;
}

.stButton > button {
    border-radius: 10px;
    font-weight: 700;
}

.section-title {
    font-size: 20px;
    font-weight: 750;
    color: #101828;
    margin: 28px 0 12px;
}
.section-sub {
    color: #667085;
    font-size: 12px;
    margin-top: -7px;
    margin-bottom: 14px;
}
.card {
    background: white;
    border: 1px solid #e6eaf0;
    border-radius: 15px;
    padding: 18px;
    box-shadow: 0 3px 12px rgba(15,23,42,.04);
}
.badge {
    display:inline-block;
    padding:5px 9px;
    border-radius:20px;
    font-size:11px;
    font-weight:700;
    background:#e9f8f1;
    color:#087443;
}
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e6eaf0;
    padding: 14px 16px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)


# ---------- Data ----------
@st.cache_data
def load_summary():
    if not SUMMARY_FILE.exists():
        return {}
    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_csv(path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

@st.cache_data
def load_audit():
    if not AUDIT_FILE.exists():
        return pd.DataFrame()
    try:
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if isinstance(obj, list):
            return pd.DataFrame(obj)
        return pd.DataFrame([obj])
    except Exception:
        return pd.DataFrame()

summary = load_summary()
results = load_csv(RESULTS_FILE)
payments = load_csv(PAYMENTS_FILE)
audit = load_audit()

# ---------- Safe helpers ----------
def money(x):
    return f"₹{float(x):,.0f}"

def money_lakh(x):
    return f"₹{float(x)/100000:,.2f} L"

def pct(x):
    return f"{float(x)*100:.2f}%"

def get_action_df():
    rows = []
    for action, m in summary.get("action_metrics", {}).items():
        rows.append({
            "Action": action.replace("_", " ").title(),
            "Payments": int(m.get("payments", 0)),
            "Successful Recoveries": int(m.get("successful_recoveries", 0)),
            "Revenue Recovered": float(m.get("revenue_recovered", 0)),
            "Recovery Rate": float(m.get("recovery_rate", 0)) * 100,
        })
    return pd.DataFrame(rows)

def get_failure_df():
    rows = []
    for reason, m in summary.get("failure_metrics", {}).items():
        rows.append({
            "Failure Reason": reason.replace("_", " ").title(),
            "Payments": int(m.get("payments", 0)),
            "Revenue at Risk": float(m.get("revenue_at_risk", 0)),
            "RecoverAI Revenue": float(m.get("recoverai_revenue", 0)),
            "Successful Recoveries": int(m.get("successful_recoveries", 0)),
        })
    return pd.DataFrame(rows)

action_df = get_action_df()
failure_df = get_failure_df()

# ---------- Core values ----------
risk = summary.get("total_revenue_at_risk", 0)
baseline_rev = summary.get("baseline_recovered_revenue", 0)
ai_rev = summary.get("recoverai_recovered_revenue", 0)
incremental = summary.get("incremental_revenue_vs_baseline", 0)
baseline_rate = summary.get("baseline_recovery_rate", 0)
ai_rate = summary.get("recoverai_recovery_rate", 0)
baseline_count = summary.get("baseline_successful_recoveries", 0)
ai_count = summary.get("recoverai_successful_recoveries", 0)
allowed = summary.get("recoverai_allowed_actions", 0)
human = summary.get("human_escalations", 0)
blocked = summary.get("blocked_actions", 0)
stopped = summary.get("stopped_actions", 0)


# ---------- Audit record generator ----------
def generate_evaluation_audit_records(df, limit=100):
    """Create transparent audit records from the existing synthetic evaluation."""
    if df.empty:
        return []

    def first_value(row, names, default=None):
        for name in names:
            if name in row.index and pd.notna(row[name]):
                return row[name]
        return default

    records = []
    sample = df.head(limit).copy()

    for _, row in sample.iterrows():
        amount = first_value(row, ["amount", "Amount"], 0)
        probability = first_value(
            row,
            ["recovery_probability", "recover_probability", "predicted_probability", "probability"],
            None,
        )
        action = first_value(
            row,
            ["recommended_action", "action", "decision", "selected_action"],
            "UNKNOWN",
        )
        recovered = first_value(
            row,
            ["recovered", "success", "recovery_success", "recovered_flag"],
            False,
        )
        recovered_amount = first_value(
            row,
            ["recovered_amount", "revenue_recovered", "recoverai_recovered_amount"],
            0,
        )
        failure_reason = first_value(
            row,
            ["failure_reason", "Failure Reason"],
            "UNKNOWN",
        )
        payment_id = first_value(row, ["payment_id", "Payment ID"], "unknown")
        customer_id = first_value(row, ["customer_id", "Customer ID"], "unknown")
        merchant_id = first_value(row, ["merchant_id", "Merchant ID"], "unknown")

        try:
            amount = float(amount)
        except Exception:
            amount = 0.0

        try:
            probability = float(probability) if probability is not None else None
        except Exception:
            probability = None

        try:
            recovered_amount = float(recovered_amount)
        except Exception:
            recovered_amount = 0.0

        if isinstance(recovered, str):
            recovered = recovered.strip().lower() in {"true", "1", "yes", "success", "recovered"}

        # The evaluation is synthetic, so make that explicit in the audit record.
        record = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "payment_id": str(payment_id),
            "customer_id": str(customer_id),
            "merchant_id": str(merchant_id),
            "amount": amount,
            "failure_reason": str(failure_reason),
            "ml_recovery_probability": probability,
            "expected_recovery_value": (
                amount * probability if probability is not None else None
            ),
            "recommended_action": str(action),
            "policy_status": "EVALUATION_SIMULATION",
            "policy_allowed": True,
            "policy_reason": "Synthetic evaluation audit record; not a live payment authorization.",
            "execution_status": "SIMULATED_SUCCESS" if recovered else "SIMULATED_NO_RECOVERY",
            "recovered": bool(recovered),
            "recovered_amount": recovered_amount,
            "source": "synthetic_action_aware_evaluation",
        }
        records.append(record)

    return records


def save_evaluation_audit_records(records):
    """Append generated records to api/audit_log.json without breaking existing logs."""
    existing = []
    if AUDIT_FILE.exists():
        try:
            with open(AUDIT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                existing = data
            elif isinstance(data, dict):
                existing = [data]
        except Exception:
            existing = []

    existing.extend(records)

    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, default=str)

    return len(existing)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("""
    <div class="brand">
        <div class="brand-title">RECOVER<span>AI</span></div>
        <div class="brand-sub">AI-POWERED REVENUE RECOVERY</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "COMMAND CENTER",
        [
            "Overview",
            "Revenue Recovery",
            "AI Decision Center",
            "Failure Intelligence",
            "Payment Explorer",
            "Safety & Governance",
            "Audit Trail",
        ],
        label_visibility="visible",
    )

    st.markdown("---")
    st.markdown("**SYSTEM STATUS**")
    st.markdown("🟢 AI engine online")
    st.markdown("🟢 Policy engine active")
    st.markdown("🟢 Audit logging enabled")
    st.caption("Synthetic action-aware evaluation • Razorpay hackathon prototype")


# ============================================================
# OVERVIEW
# ============================================================
if page == "Overview":
    st.markdown("""
    <div class="hero">
        <h1>RecoverAI Revenue Command Center</h1>
        <p>Intelligent recovery decisions for failed payments — predict, act, verify, and stop safely.</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(5)
    cards = [
        ("Revenue at Risk", money_lakh(risk), "Evaluation batch"),
        ("RecoverAI Recovered", money_lakh(ai_rev), "AI-assisted recovery"),
        ("Incremental Revenue", money_lakh(incremental), "vs baseline"),
        ("Recovery Rate", pct(ai_rate), "Evaluation recovery"),
        ("Successful Recoveries", f"{ai_count:,}", "RecoverAI"),
    ]
    for c, (label, value, note) in zip(cols, cards):
        with c:
            st.markdown(f"""
            <div class="kpi">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-note">↑ {note}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Business Impact</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">RecoverAI is evaluated against a no-AI baseline on the same evaluation batch.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        chart_df = pd.DataFrame({
            "System": ["Baseline", "RecoverAI"],
            "Revenue Recovered": [baseline_rev, ai_rev]
        })
        fig = px.bar(
            chart_df, x="System", y="Revenue Recovered",
            text="Revenue Recovered", title="Revenue recovered: baseline vs RecoverAI"
        )
        fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig.update_layout(
            height=390, margin=dict(l=10,r=10,t=55,b=10),
            yaxis_title="Revenue recovered (₹)", xaxis_title=""
        )
        st.plotly_chart(fig, width="stretch")

    with c2:
        funnel = pd.DataFrame({
            "Stage": ["Revenue at Risk", "Baseline Recovery", "RecoverAI Recovery"],
            "Amount": [risk, baseline_rev, ai_rev]
        })
        fig = px.bar(
            funnel, x="Stage", y="Amount",
            text="Amount", title="Recovery funnel"
        )
        fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig.update_layout(
            height=390, margin=dict(l=10,r=10,t=55,b=10),
            yaxis_title="Amount (₹)", xaxis_title=""
        )
        st.plotly_chart(fig, width="stretch")

    st.markdown('<div class="section-title">Recovery Engine Snapshot</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Allowed actions", f"{allowed:,}")
    with c2:
        st.metric("Human escalations", f"{human:,}")
    with c3:
        st.metric("Stopped", f"{stopped:,}")
    with c4:
        st.metric("Blocked", f"{blocked:,}")

    st.info("31.83% is the action-aware evaluation recovery rate, not ML model accuracy. Model quality is reported separately in the AI Decision Center.")


# ============================================================
# REVENUE RECOVERY
# ============================================================
elif page == "Revenue Recovery":
    st.markdown('<div class="hero"><h1>Revenue Recovery</h1><p>Measure the money RecoverAI protects and the incremental value generated over the baseline.</p></div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("At risk", money_lakh(risk))
    c2.metric("Baseline", money_lakh(baseline_rev))
    c3.metric("RecoverAI", money_lakh(ai_rev))
    c4.metric("Incremental", money_lakh(incremental))

    st.markdown('<div class="section-title">Recovery by intervention</div>', unsafe_allow_html=True)

    if not action_df.empty:
        c1, c2 = st.columns(2)

        with c1:
            fig = px.bar(
                action_df.sort_values("Revenue Recovered", ascending=True),
                x="Revenue Recovered", y="Action", orientation="h",
                text="Revenue Recovered",
                title="Revenue recovered by action"
            )
            fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
            fig.update_layout(height=430, margin=dict(l=10,r=30,t=55,b=10))
            st.plotly_chart(fig, width="stretch")

        with c2:
            fig = px.bar(
                action_df.sort_values("Recovery Rate", ascending=True),
                x="Recovery Rate", y="Action", orientation="h",
                text="Recovery Rate",
                title="Recovery rate by action"
            )
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(height=430, margin=dict(l=10,r=30,t=55,b=10), xaxis_title="Recovery rate (%)")
            st.plotly_chart(fig, width="stretch")

        display = action_df.copy()
        display["Revenue Recovered"] = display["Revenue Recovered"].map(money)
        display["Recovery Rate"] = display["Recovery Rate"].map(lambda x: f"{x:.2f}%")
        st.dataframe(display, width="stretch", hide_index=True)


# ============================================================
# AI DECISION CENTER
# ============================================================
elif page == "AI Decision Center":
    st.markdown('<div class="hero"><h1>AI Decision Center</h1><p>Every failed payment is scored and routed through a bounded recovery policy.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Decision distribution</div>', unsafe_allow_html=True)

    if not action_df.empty:
        c1, c2 = st.columns(2)

        with c1:
            fig = px.pie(
                action_df, names="Action", values="Payments",
                hole=.58, title="Recovery actions selected"
            )
            fig.update_layout(height=420, margin=dict(l=10,r=10,t=55,b=10))
            st.plotly_chart(fig, width="stretch")

        with c2:
            fig = px.bar(
                action_df.sort_values("Payments", ascending=True),
                x="Payments", y="Action", orientation="h",
                text="Payments", title="Actions by payment count"
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(height=420, margin=dict(l=10,r=30,t=55,b=10))
            st.plotly_chart(fig, width="stretch")

    st.markdown('<div class="section-title">ML model performance</div>', unsafe_allow_html=True)
    st.caption("These are model-classification metrics and should not be confused with the 31.83% action-aware recovery rate.")

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Accuracy", "67.65%")
    mc2.metric("F1 score", "71.21%")
    mc3.metric("ROC-AUC", "72.42%")

    st.markdown('<div class="section-title">Decision policy</div>', unsafe_allow_html=True)
    policy = pd.DataFrame([
        ["Retry", "≥ 70% probability", "Temporary failures", "Max 2 retries"],
        ["Payment reminder", "45–70%", "Recovery opportunity", "Bounded"],
        ["Update payment method", "Card expired", "Permanent payment issue", "Customer action"],
        ["Human review", "Policy escalation", "High-value / uncertain", "Human required"],
        ["Stop", "< 45% / retry limit", "Low-value opportunity", "No further action"],
    ], columns=["Action","Trigger","Context","Safety control"])
    st.dataframe(policy.astype(str), width="stretch", hide_index=True)


# ============================================================
# FAILURE INTELLIGENCE
# ============================================================
elif page == "Failure Intelligence":
    st.markdown('<div class="hero"><h1>Failure Intelligence</h1><p>Understand where revenue is being lost and which failure modes offer the strongest recovery opportunities.</p></div>', unsafe_allow_html=True)

    if not failure_df.empty:
        c1, c2 = st.columns(2)

        with c1:
            fig = px.bar(
                failure_df.sort_values("Revenue at Risk", ascending=True),
                x="Revenue at Risk", y="Failure Reason", orientation="h",
                text="Revenue at Risk", title="Revenue at risk by failure reason"
            )
            fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
            fig.update_layout(height=450, margin=dict(l=10,r=30,t=55,b=10))
            st.plotly_chart(fig, width="stretch")

        with c2:
            fig = px.bar(
                failure_df.sort_values("RecoverAI Revenue", ascending=True),
                x="RecoverAI Revenue", y="Failure Reason", orientation="h",
                text="RecoverAI Revenue", title="RecoverAI revenue recovered by failure"
            )
            fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
            fig.update_layout(height=450, margin=dict(l=10,r=30,t=55,b=10))
            st.plotly_chart(fig, width="stretch")

        display = failure_df.copy()
        for col in ["Revenue at Risk", "RecoverAI Revenue"]:
            display[col] = display[col].map(money)
        st.dataframe(display.astype(str), width="stretch", hide_index=True)


# ============================================================
# PAYMENT EXPLORER
# ============================================================
elif page == "Payment Explorer":
    st.markdown('<div class="hero"><h1>Payment Explorer</h1><p>Inspect individual failed payments, recovery decisions, and outcomes.</p></div>', unsafe_allow_html=True)

    if results.empty:
        st.warning("batch_results.csv was not found.")
    else:
        df = results.copy()

        search = st.text_input("Search payment / customer / merchant ID", "")
        reasons = sorted(df["failure_reason"].dropna().astype(str).unique()) if "failure_reason" in df else []
        selected_reason = st.selectbox("Failure reason", ["All"] + reasons)

        if search:
            mask = df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False))
            df = df[mask.any(axis=1)]

        if selected_reason != "All" and "failure_reason" in df:
            df = df[df["failure_reason"].astype(str) == selected_reason]

        st.caption(f"{len(df):,} payments shown")

        # Normalize every display column to string to prevent Arrow mixed-type errors.
        display = df.head(500).copy()
        for col in display.columns:
            display[col] = display[col].astype(str)

        st.dataframe(display, width="stretch", height=520, hide_index=True)


# ============================================================
# SAFETY & GOVERNANCE
# ============================================================
elif page == "Safety & Governance":
    st.markdown('<div class="hero"><h1>Safety & Governance</h1><p>RecoverAI is designed to act within explicit limits, escalate uncertainty, and stop when recovery should no longer be attempted.</p></div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Max auto retries", "2")
    c2.metric("Retry threshold", "70%")
    c3.metric("High-value threshold", "₹10,000")
    c4.metric("Blocked actions", f"{blocked:,}")

    st.markdown('<div class="section-title">Governance controls</div>', unsafe_allow_html=True)

    controls = pd.DataFrame([
        ["Retry limit", "2 automatic retries", "Prevents repeated payment attempts"],
        ["Probability gate", "≥ 70% for automatic retry", "Limits low-confidence automation"],
        ["Temporary-failure gate", "Timeout / network only", "Avoids unsafe retry of permanent failures"],
        ["High-value protection", "> ₹10,000", "Routes sensitive cases for escalation"],
        ["Human review", f"{human:,} cases", "Human decision for uncertain/high-risk cases"],
        ["Stop control", f"{stopped:,} cases", "Ends recovery when further action is not justified"],
        ["Audit trail", "Enabled", "Records decision and execution context"],
    ], columns=["Control","Configuration","Purpose"])
    st.dataframe(controls.astype(str), width="stretch", hide_index=True)

    st.success("Safety posture: policy-gated automation with human escalation and explicit stopping rules.")


# ============================================================
# AUDIT TRAIL
# ============================================================
elif page == "Audit Trail":
    st.markdown('<div class="hero"><h1>Audit Trail</h1><p>Trace recovery decisions from payment context through policy evaluation and simulated outcome.</p></div>', unsafe_allow_html=True)

    st.info(
        "These records are generated from the synthetic action-aware evaluation. "
        "They demonstrate auditability and are not live Razorpay payment authorizations."
    )

    if not results.empty:
        c1, c2, c3 = st.columns([1, 1, 2])

        with c1:
            sample_size = st.selectbox(
                "Records to generate",
                [25, 50, 100, 250, 500],
                index=2,
            )

        with c2:
            if st.button("Generate audit records", type="primary"):
                records = generate_evaluation_audit_records(results, sample_size)
                total = save_evaluation_audit_records(records)
                st.success(f"Added {len(records):,} audit records. Total stored: {total:,}.")
                st.cache_data.clear()
                st.rerun()

        with c3:
            st.caption(
                "Each record captures payment context, recovery probability when available, "
                "recommended action, evaluation status, and recovered amount."
            )

    audit = load_audit()

    if audit.empty:
        st.warning("No audit records are currently available. Use the button above to generate transparent evaluation records.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Audit records", f"{len(audit):,}")
        recovered_records = 0
        if "recovered" in audit.columns:
            recovered_records = audit["recovered"].astype(str).str.lower().isin(
                ["true", "1", "yes", "recovered"]
            ).sum()
        c2.metric("Recovered records", f"{recovered_records:,}")

        if "recovered_amount" in audit.columns:
            total_logged = pd.to_numeric(audit["recovered_amount"], errors="coerce").fillna(0).sum()
        else:
            total_logged = 0
        c3.metric("Logged recovered value", money_lakh(total_logged))

        st.markdown('<div class="section-title">Decision trace</div>', unsafe_allow_html=True)

        display = audit.copy()

        # Keep the most useful columns first when available.
        preferred = [
            "timestamp",
            "payment_id",
            "amount",
            "failure_reason",
            "ml_recovery_probability",
            "expected_recovery_value",
            "recommended_action",
            "policy_status",
            "execution_status",
            "recovered",
            "recovered_amount",
        ]
        ordered = [c for c in preferred if c in display.columns]
        ordered += [c for c in display.columns if c not in ordered]
        display = display[ordered].tail(500).copy()

        for col in display.columns:
            display[col] = display[col].astype(str)

        st.dataframe(display, width="stretch", height=560, hide_index=True)


# ---------- Footer ----------
st.markdown("---")
st.caption("RECOVERAI • AI Revenue Recovery • Synthetic action-aware evaluation • Prototype for Razorpay hackathon")
