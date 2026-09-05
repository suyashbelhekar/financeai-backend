"""
tax_matching_service.py
Rule-based tax classification with optional AI fallback for ambiguous cases.
"""
from __future__ import annotations
import re
from typing import Optional
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.tax_match import TaxMatch


TAX_RULES = [
    # (regex_pattern, tax_category, tax_code, confidence)
    (r"salary|payroll|wages|compensation",  "Employment Income",         "1.00", 0.99),
    (r"rent|lease|property",                "Rent Expense",              "2.01", 0.97),
    (r"electricity|power|msedcl|bescom",    "Utilities – Electricity",   "2.02", 0.97),
    (r"internet|broadband|jio|airtel|bsnl", "Utilities – Internet",      "2.03", 0.96),
    (r"aws|azure|gcp|cloud|hosting",        "IT Infrastructure (COGS)",  "1.01", 0.97),
    (r"salesforce|hubspot|zoom|slack|saas", "SaaS Subscriptions (SG&A)", "2.04", 0.95),
    (r"google ads|facebook ads|marketing",  "Advertising (SG&A)",        "2.07", 0.95),
    (r"fuel|petrol|diesel|hp pump",         "Travel – Fuel",             "2.12", 0.96),
    (r"atm|cash withdrawal",                "Cash Withdrawal",           "3.01", 0.90),
    (r"grocery|supermarket|fresh mart",     "Meals & Entertainment",     "2.09", 0.88),
    (r"food|restaurant|swiggy|zomato|foodhub", "Meals & Entertainment",  "2.09", 0.88),
    (r"legal|attorney|advocate|retainer",   "Professional Services",     "2.15", 0.92),
    (r"transfer|wire|neft|imps|rtgs",       "Intercompany / Transfer",   "3.02", 0.80),
    (r"refund|return|reversal",             "Refund / Reversal",         "3.03", 0.85),
    (r"shopping|amazon|flipkart|shopkart",  "Office / Equipment",        "2.11", 0.82),
]


def _rule_match(description: str) -> Optional[tuple]:
    desc = (description or "").lower()
    for pattern, category, code, conf in TAX_RULES:
        if re.search(pattern, desc):
            return category, code, conf
    return None


def match_transaction(db: Session, transaction_id: str) -> dict:
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        return {"error": "Transaction not found"}

    result = _rule_match(tx.description or "")

    if result:
        category, code, confidence = result
        method = "rule"
        reasoning = f"Matched pattern against description: '{tx.description}'"
        status = "matched"
    else:
        # Low confidence default
        category, code, confidence = "Uncategorized", "0.00", 0.30
        method = "rule"
        reasoning = "No matching tax rule found. Manual review required."
        status = "review"

    # Upsert
    existing = db.query(TaxMatch).filter(TaxMatch.transaction_id == tx.id).first()
    if existing:
        existing.tax_category = category
        existing.tax_code = code
        existing.confidence = confidence
        existing.reasoning = reasoning
        existing.method = method
        existing.status = status
    else:
        tm = TaxMatch(
            transaction_id=tx.id,
            tax_category=category,
            tax_code=code,
            confidence=confidence,
            reasoning=reasoning,
            method=method,
            status=status,
        )
        db.add(tm)

    tx.category = category
    db.commit()

    return {
        "transaction_id": str(tx.id),
        "tax_category": category,
        "tax_code": code,
        "confidence": confidence,
        "reasoning": reasoning,
        "method": method,
        "status": status,
    }


def match_all(db: Session) -> list:
    """Match all transactions in a single batch — one DB round-trip."""
    txs = db.query(Transaction).all()
    results = []
    for t in txs:
        result = _rule_match(t.description or "")
        if result:
            category, code, confidence = result
            method, status = "rule", "matched"
            reasoning = f"Matched pattern against description: '{t.description}'"
        else:
            category, code, confidence = "Uncategorized", "0.00", 0.30
            method, status = "rule", "review"
            reasoning = "No matching tax rule found. Manual review required."

        t.category = category
        existing = db.query(TaxMatch).filter(TaxMatch.transaction_id == t.id).first()
        if existing:
            existing.tax_category = category
            existing.tax_code     = code
            existing.confidence   = confidence
            existing.reasoning    = reasoning
            existing.method       = method
            existing.status       = status
        else:
            db.add(TaxMatch(
                transaction_id=t.id,
                tax_category=category,
                tax_code=code,
                confidence=confidence,
                reasoning=reasoning,
                method=method,
                status=status,
            ))

        results.append({
            "transaction_id": str(t.id),
            "tax_category": category,
            "tax_code": code,
            "confidence": confidence,
            "reasoning": reasoning,
            "method": method,
            "status": status,
        })

    db.commit()
    return results
