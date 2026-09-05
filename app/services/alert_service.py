from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.alert import Alert
from app.models.transaction import Transaction
from app.models.account import Account


def list_alerts(db: Session) -> list:
    return db.query(Alert).order_by(Alert.created_at.desc()).all()


def mark_read(db: Session, alert_id: str) -> Alert:
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if a:
        a.status = "read"
        db.commit()
        db.refresh(a)
    return a


def auto_generate_alerts(db: Session) -> int:
    """Generate system alerts based on current DB state. Returns count created."""
    created = 0

    # High-value unmatched
    high_unmatched = db.query(Transaction).filter(
        Transaction.status == "unmatched",
        Transaction.amount >= 10000,
    ).all()
    for tx in high_unmatched:
        exists = db.query(Alert).filter(
            Alert.type == "unmatched_high_value",
            Alert.title.contains(tx.transaction_id),
        ).first()
        if not exists:
            db.add(Alert(
                type="unmatched_high_value",
                severity="critical",
                title=f"High-Value Unmatched: {tx.transaction_id}",
                message=f"Transaction {tx.transaction_id} for ₹{tx.amount:,.0f} "
                        f"({tx.description}) is unmatched.",
            ))
            created += 1

    # Reconciliation failure rate
    total = db.query(func.count(Transaction.id)).scalar() or 0
    unmatched = db.query(func.count(Transaction.id)).filter(
        Transaction.status == "unmatched"
    ).scalar() or 0
    if total > 0 and unmatched / total > 0.1:
        exists = db.query(Alert).filter(Alert.type == "recon_rate_low").first()
        if not exists:
            db.add(Alert(
                type="recon_rate_low",
                severity="warning",
                title="Reconciliation Rate Below 90%",
                message=f"{unmatched}/{total} transactions unmatched "
                        f"({unmatched/total*100:.1f}% failure rate).",
            ))
            created += 1

    # Low balance
    total_balance = db.query(func.sum(Account.current_balance)).scalar() or 0
    if total_balance < 100000:
        exists = db.query(Alert).filter(Alert.type == "low_balance").first()
        if not exists:
            db.add(Alert(
                type="low_balance",
                severity="warning",
                title="Low Cash Balance",
                message=f"Total balance is ₹{total_balance:,.0f}. Review upcoming payments.",
            ))
            created += 1

    # Disputed transactions
    disputed = db.query(func.count(Transaction.id)).filter(
        Transaction.status == "disputed"
    ).scalar() or 0
    if disputed > 0:
        exists = db.query(Alert).filter(Alert.type == "disputed_transactions").first()
        if not exists:
            db.add(Alert(
                type="disputed_transactions",
                severity="warning",
                title=f"{disputed} Disputed Transactions",
                message=f"{disputed} transactions are in dispute status and require review.",
            ))
            created += 1

    db.commit()
    return created
