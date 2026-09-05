"""
Reconciliation engine using deterministic rule-based scoring.
Compares transactions within the same account across sources.
"""
from __future__ import annotations
import time
from difflib import SequenceMatcher
from datetime import timedelta
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.reconciliation import ReconciliationRecord


def _text_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _score_pair(tx_a: Transaction, tx_b: Transaction) -> Tuple[float, str]:
    """
    Return (score 0-100, method) for a pair of transactions.
    """
    score = 0.0
    method = "fuzzy"

    # 1. Exact transaction ID match (highest confidence)
    if tx_a.transaction_id and tx_b.transaction_id:
        if tx_a.transaction_id == tx_b.transaction_id:
            return 100.0, "exact_id"

    # 2. Exact amount (30 pts)
    if abs(tx_a.amount - tx_b.amount) < 0.01:
        score += 30
    elif abs(tx_a.amount - tx_b.amount) / max(tx_a.amount, 1) < 0.01:
        score += 20   # within 1%

    # 3. Same direction (10 pts)
    if tx_a.direction == tx_b.direction:
        score += 10

    # 4. Date proximity (max 25 pts)
    delta = abs((tx_a.transaction_date - tx_b.transaction_date).days)
    if delta == 0:
        score += 25
    elif delta <= 1:
        score += 20
    elif delta <= 3:
        score += 10
    elif delta > 7:
        score -= 20   # penalise large gap

    # 5. Description similarity (max 25 pts)
    sim = _text_similarity(tx_a.description or "", tx_b.description or "")
    score += sim * 25

    # 6. Merchant match (10 pts)
    if tx_a.merchant and tx_b.merchant:
        if _text_similarity(tx_a.merchant, tx_b.merchant) > 0.8:
            score += 10

    return max(0.0, min(100.0, score)), method


def _classify(score: float) -> str:
    if score >= 95:
        return "matched"
    if score >= 75:
        return "probable"
    if score >= 40:
        return "unmatched"
    return "unmatched"


def run_reconciliation(db: Session, account_id: str = None) -> dict:
    start = time.time()

    q = db.query(Transaction)
    if account_id:
        q = q.filter(Transaction.account_id == account_id)

    # Only try to reconcile bank-sourced vs processor-sourced transactions
    bank_txs = q.filter(Transaction.source == "bank_csv").all()
    proc_txs = q.filter(Transaction.source.in_(["processor_csv", "manual"])).all()

    # If all are same source, compare within the set
    if not proc_txs:
        all_txs = bank_txs
        candidates = all_txs
    else:
        candidates = proc_txs

    stats = {"matched": 0, "probable": 0, "unmatched": 0, "disputed": 0}
    matched_ids: set = set()

    for tx_a in bank_txs:
        best_score = 0.0
        best_match = None
        best_method = "fuzzy"

        for tx_b in candidates:
            if tx_a.id == tx_b.id or tx_b.id in matched_ids:
                continue
            score, method = _score_pair(tx_a, tx_b)
            if score > best_score:
                best_score = score
                best_match = tx_b
                best_method = method

        status = _classify(best_score)
        diff = abs(tx_a.amount - best_match.amount) if best_match else 0.0

        # Upsert reconciliation record
        existing = db.query(ReconciliationRecord).filter(
            ReconciliationRecord.transaction_id == tx_a.id
        ).first()

        if existing:
            existing.matching_score = best_score
            existing.matching_method = best_method
            existing.status = status
            existing.difference = diff
            existing.matched_transaction_id = best_match.id if best_match else None
        else:
            rec = ReconciliationRecord(
                transaction_id=tx_a.id,
                matched_transaction_id=best_match.id if best_match else None,
                matching_score=best_score,
                matching_method=best_method,
                status=status,
                difference=diff,
            )
            db.add(rec)

        # Update transaction status
        tx_a.status = "reconciled" if status in ("matched", "probable") else "unmatched"

        if best_match and status in ("matched", "probable"):
            matched_ids.add(best_match.id)

        stats[status] = stats.get(status, 0) + 1

    db.commit()
    duration = round(time.time() - start, 3)

    return {
        "total_processed": len(bank_txs),
        "matched": stats.get("matched", 0),
        "probable": stats.get("probable", 0),
        "unmatched": stats.get("unmatched", 0),
        "disputed": stats.get("disputed", 0),
        "duration_seconds": duration,
    }
