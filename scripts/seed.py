"""
seed.py — Clean minimal demo data for FinanceAI.
3-4 records per entity. No faker. No random data.
Run: python scripts/seed.py  (from financeai/backend/)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from app.database import SessionLocal, create_tables
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.reconciliation import ReconciliationRecord
from app.models.tax_match import TaxMatch
from app.models.alert import Alert
from app.models.ai_insight import AIInsight
from app.models.forecast import Forecast
from app.models.settings import UserSettings
from app.utils.security import hash_password

create_tables()
db = SessionLocal()

print("🧹  Clearing existing data...")
for model in [TaxMatch, ReconciliationRecord, AIInsight, Alert, Forecast,
              Transaction, Account, UserSettings, User]:
    db.query(model).delete()
db.commit()

# ── User ──────────────────────────────────────────────────────────────────
print("👤  Creating demo user...")
user = User(
    name="Demo User",
    email="demo@financeai.com",
    password_hash=hash_password("demo1234"),
    role="admin",
)
db.add(user)
db.flush()

db.add(UserSettings(
    user_id=user.id,
    currency="INR",
    forecast_period=6,
    reconciliation_threshold=85,
    notify_critical=True,
    notify_warnings=True,
    notify_digest=True,
))

# ── Accounts (3) ──────────────────────────────────────────────────────────
print("🏦  Creating accounts...")
acc_ops = Account(
    user_id=user.id,
    account_name="Operating Account",
    account_type="Checking",
    institution="HDFC Bank",
    currency="INR",
    current_balance=284000.0,
    status="active",
)
acc_tax = Account(
    user_id=user.id,
    account_name="Tax Reserve",
    account_type="Savings",
    institution="SBI",
    currency="INR",
    current_balance=92000.0,
    status="active",
)
acc_pay = Account(
    user_id=user.id,
    account_name="Stripe Payments",
    account_type="Payments",
    institution="Stripe",
    currency="INR",
    current_balance=48700.0,
    status="active",
)
db.add_all([acc_ops, acc_tax, acc_pay])
db.flush()

# ── Transactions (4) ──────────────────────────────────────────────────────
print("💳  Creating transactions...")
txns = [
    Transaction(
        account_id=acc_ops.id,
        transaction_id="TXN-2026-001",
        transaction_date=date(2026, 9, 1),
        description="Salary Credit — September",
        merchant="ACME Pvt Ltd",
        amount=150000.0,
        direction="CREDIT",
        transaction_type="NEFT",
        currency="INR",
        category="Employment Income",
        source="bank_csv",
        status="reconciled",
        balance_after=284000.0,
    ),
    Transaction(
        account_id=acc_ops.id,
        transaction_id="TXN-2026-002",
        transaction_date=date(2026, 9, 2),
        description="Office Rent — September",
        merchant="ABC Properties",
        amount=45000.0,
        direction="DEBIT",
        transaction_type="NEFT",
        currency="INR",
        category="Rent Expense",
        source="bank_csv",
        status="reconciled",
        balance_after=239000.0,
    ),
    Transaction(
        account_id=acc_pay.id,
        transaction_id="TXN-2026-003",
        transaction_date=date(2026, 9, 3),
        description="Stripe Payout — Aug Sales",
        merchant="Stripe",
        amount=48700.0,
        direction="CREDIT",
        transaction_type="UPI",
        currency="INR",
        category="Revenue",
        source="processor_csv",
        status="pending",
        balance_after=48700.0,
    ),
    Transaction(
        account_id=acc_ops.id,
        transaction_id="TXN-2026-004",
        transaction_date=date(2026, 9, 4),
        description="AWS Cloud Services",
        merchant="Amazon Web Services",
        amount=12300.0,
        direction="DEBIT",
        transaction_type="IMPS",
        currency="INR",
        category="IT Infrastructure (COGS)",
        source="bank_csv",
        status="unmatched",
        balance_after=226700.0,
    ),
]
db.add_all(txns)
db.flush()

# ── Reconciliation records (2) ────────────────────────────────────────────
print("🔗  Creating reconciliation records...")
db.add(ReconciliationRecord(
    transaction_id=txns[0].id,
    matched_transaction_id=None,
    matching_score=98.5,
    matching_method="exact_id",
    status="matched",
    difference=0.0,
    notes="Exact match on transaction ID and amount",
))
db.add(ReconciliationRecord(
    transaction_id=txns[3].id,
    matched_transaction_id=None,
    matching_score=42.0,
    matching_method="fuzzy",
    status="unmatched",
    difference=0.0,
    notes="No matching processor record found for AWS invoice",
))

# ── Tax matches (3) ───────────────────────────────────────────────────────
print("🧾  Creating tax matches...")
tax_data = [
    (txns[0], "Employment Income",         "1.00", 0.99, "rule", "matched",
     "Matched keyword: salary/credit"),
    (txns[1], "Rent Expense",              "2.01", 0.97, "rule", "matched",
     "Matched keyword: rent/lease"),
    (txns[3], "IT Infrastructure (COGS)",  "1.01", 0.96, "rule", "matched",
     "Matched keyword: aws/cloud/hosting"),
]
for tx, cat, code, conf, method, status, reason in tax_data:
    db.add(TaxMatch(
        transaction_id=tx.id,
        tax_category=cat,
        tax_code=code,
        confidence=conf,
        reasoning=reason,
        method=method,
        status=status,
    ))

# ── Alerts (3) ────────────────────────────────────────────────────────────
print("🔔  Creating alerts...")
db.add_all([
    Alert(
        type="unmatched_transaction",
        severity="warning",
        title="Unmatched Transaction Detected",
        message="TXN-2026-004 (AWS Cloud Services ₹12,300) has no matching processor record. Review and reconcile manually.",
        status="unread",
    ),
    Alert(
        type="pending_settlement",
        severity="info",
        title="Stripe Payout Pending",
        message="TXN-2026-003 (₹48,700 from Stripe) is pending reconciliation. Expected settlement within 2 business days.",
        status="unread",
    ),
    Alert(
        type="recon_complete",
        severity="success",
        title="Reconciliation Run Complete",
        message="4 transactions processed. 2 matched, 1 pending, 1 unmatched. Overall match rate: 50%.",
        status="read",
    ),
])

# ── AI Insights (3) ───────────────────────────────────────────────────────
print("🤖  Creating AI insights...")
db.add_all([
    AIInsight(
        insight_type="reconciliation",
        title="Reconciliation Rate at 50%",
        description="2 of 4 transactions are reconciled. TXN-2026-004 (AWS, ₹12,300) is unmatched and TXN-2026-003 (Stripe, ₹48,700) is pending. Run the reconciliation engine after uploading the processor settlement file.",
        severity="warning",
    ),
    AIInsight(
        insight_type="cash_flow",
        title="Net Cash Position: ₹4,24,700",
        description="Total balance across 3 accounts is ₹4,24,700. Operating account holds ₹2,84,000 (67%). Salary inflow of ₹1,50,000 offset by rent ₹45,000 and AWS ₹12,300 this month.",
        severity="info",
    ),
    AIInsight(
        insight_type="tax",
        title="3 Transactions Tax-Classified",
        description="Rule-based engine classified: Salary → Employment Income (1.00), Rent → Rent Expense (2.01), AWS → IT Infrastructure COGS (1.01). All at 96–99% confidence. No manual review needed.",
        severity="success",
    ),
])

# ── Forecast (3 months) ───────────────────────────────────────────────────
print("📈  Creating forecast...")
forecast_data = [
    (date(2026, 10, 1), 160000, 60000, 364700, 0.82),
    (date(2026, 11, 1), 165000, 58000, 471700, 0.80),
    (date(2026, 12, 1), 170000, 62000, 579700, 0.78),
]
for fd, inflow, outflow, balance, conf in forecast_data:
    db.add(Forecast(
        forecast_date=fd,
        predicted_inflow=inflow,
        predicted_outflow=outflow,
        predicted_balance=balance,
        confidence=conf,
        model_version="linear_v1",
        scenario="base",
    ))

db.commit()

print()
print("✅  Seed complete!")
print()
print("   Accounts    : 3  (Operating, Tax Reserve, Stripe)")
print("   Transactions: 4  (2 reconciled, 1 pending, 1 unmatched)")
print("   Recon records: 2")
print("   Tax matches  : 3")
print("   Alerts       : 3")
print("   AI Insights  : 3")
print("   Forecasts    : 3 months")
print()
print("   Login → demo@financeai.com / demo1234")
print("   API   → http://localhost:8001/docs")
