from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date, timedelta
from app.models.transaction import Transaction
from app.models.reconciliation import ReconciliationRecord
from app.models.ai_insight import AIInsight
from app.models.account import Account
import calendar


def get_dashboard_summary(db: Session) -> dict:
    # ── Balances ──────────────────────────────────────────────────────────
    total_balance = db.query(func.sum(Account.current_balance)).scalar() or 0.0

    # ── Reconciliation counts ─────────────────────────────────────────────
    total_tx = db.query(func.count(Transaction.id)).scalar() or 0
    reconciled = db.query(func.count(Transaction.id)).filter(
        Transaction.status == "reconciled"
    ).scalar() or 0
    unmatched = db.query(func.count(Transaction.id)).filter(
        Transaction.status == "unmatched"
    ).scalar() or 0
    disputed = db.query(func.count(Transaction.id)).filter(
        Transaction.status == "disputed"
    ).scalar() or 0
    recon_rate = round((reconciled / total_tx * 100) if total_tx else 0.0, 1)

    # ── Recovery amount (sum of disputed CREDIT transactions) ──────────────
    recovery = db.query(func.sum(Transaction.amount)).filter(
        Transaction.direction == "CREDIT",
        Transaction.status == "disputed",
    ).scalar() or 0.0

    # ── Recent transactions ───────────────────────────────────────────────
    recent = (
        db.query(Transaction)
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .limit(8)
        .all()
    )

    # ── AI Insights ───────────────────────────────────────────────────────
    insights = (
        db.query(AIInsight)
        .order_by(AIInsight.generated_at.desc())
        .limit(4)
        .all()
    )

    return {
        "total_cash_balance": round(total_balance, 2),
        "reconciled_transactions": reconciled,
        "unmatched_transactions": unmatched,
        "recovery_amount": round(recovery, 2),
        "reconciliation_rate": recon_rate,
        "disputed_transactions": disputed,
        "total_transactions": total_tx,
        "recent_transactions": [_tx_to_dict(t) for t in recent],
        "ai_insights": [_insight_to_dict(i) for i in insights],
    }


def get_cash_flow(db: Session, months: int = 12) -> list:
    rows = (
        db.query(
            extract("year", Transaction.transaction_date).label("yr"),
            extract("month", Transaction.transaction_date).label("mo"),
            Transaction.direction,
            func.sum(Transaction.amount).label("total"),
        )
        .group_by("yr", "mo", Transaction.direction)
        .order_by("yr", "mo")
        .all()
    )

    # Build month buckets
    data: dict = {}
    for row in rows:
        key = (int(row.yr), int(row.mo))
        if key not in data:
            data[key] = {"inflow": 0.0, "outflow": 0.0}
        if row.direction == "CREDIT":
            data[key]["inflow"] += float(row.total)
        else:
            data[key]["outflow"] += float(row.total)

    result = []
    for (yr, mo), vals in sorted(data.items())[-months:]:
        result.append({
            "month": calendar.month_abbr[mo],
            "year": yr,
            "inflow": round(vals["inflow"], 2),
            "outflow": round(vals["outflow"], 2),
            "net": round(vals["inflow"] - vals["outflow"], 2),
        })
    return result


def _tx_to_dict(t: Transaction) -> dict:
    return {
        "id": str(t.id),
        "transaction_id": t.transaction_id,
        "date": str(t.transaction_date),
        "description": t.description,
        "merchant": t.merchant,
        "amount": f"{'+' if t.direction == 'CREDIT' else '-'}₹{t.amount:,.0f}",
        "raw_amount": t.amount,
        "direction": t.direction,
        "status": t.status,
        "category": t.category,
        "currency": t.currency,
    }


def _insight_to_dict(i: AIInsight) -> dict:
    return {
        "id": str(i.id),
        "type": i.severity,
        "title": i.title,
        "body": i.description,
    }
