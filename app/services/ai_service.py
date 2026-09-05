"""
ai_service.py
─────────────
LLM abstraction layer for FinanceAI.

Provider is selected via AI_PROVIDER env var:
  "gemini"  → Google Gemini  (google-genai SDK >= 2.x)
  "openai"  → OpenAI / any OpenAI-compatible endpoint

SECURITY:
  • GEMINI_API_KEY / OPENAI_API_KEY are read only from environment variables.
  • Keys are NEVER logged, returned in API responses, or exposed to the frontend.
  • Key validation: only existence + non-empty after strip. No format regex.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.models.transaction import Transaction
from app.models.ai_insight import AIInsight
from app.models.account import Account


# ── Provider abstraction ───────────────────────────────────────────────────

def _get_gemini_key() -> str:
    """Return stripped Gemini key or raise — no format assumption."""
    key = (settings.GEMINI_API_KEY or "").strip()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Set it in your .env file. The key is never logged or exposed."
        )
    return key


def _call_gemini(system: str, user: str) -> str:
    """Call Google Gemini using the official google-genai SDK (>= 2.x)."""
    from google import genai
    from google.genai import types

    api_key = _get_gemini_key()
    client  = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=f"{system}\n\n{user}",
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=800,
            # Disable automatic function calling to avoid internal hangs
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True,
            ),
        ),
    )
    return response.text.strip()


def _call_openai(system: str, user: str) -> str:
    """Call OpenAI (or any OpenAI-compatible endpoint)."""
    from openai import OpenAI

    key = (settings.OPENAI_API_KEY or "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.3,
        max_tokens=600,
    )
    return resp.choices[0].message.content.strip()


def _call(system: str, user: str) -> str:
    """
    Dispatch to the configured provider.
    Returns '[AI unavailable: ...]' on any error so callers never crash.
    The error message does NOT include the API key.
    """
    try:
        if settings.AI_PROVIDER == "gemini":
            return _call_gemini(system, user)
        return _call_openai(system, user)
    except Exception as exc:
        # Sanitise: remove any key-like substring before logging
        safe_msg = str(exc)
        for secret in [settings.GEMINI_API_KEY, settings.OPENAI_API_KEY]:
            if secret and secret in safe_msg:
                safe_msg = safe_msg.replace(secret, "[REDACTED]")
        return f"[AI unavailable: {safe_msg}]"


# ── Health check ──────────────────────────────────────────────────────────

def check_ai_health() -> dict:
    """
    Probe the configured AI provider with a trivial request.
    Returns status, provider, model — never the API key.
    """
    provider = settings.AI_PROVIDER
    model    = settings.GEMINI_MODEL if provider == "gemini" else settings.OPENAI_MODEL

    # Validate key exists (no format check)
    key = (settings.GEMINI_API_KEY if provider == "gemini" else settings.OPENAI_API_KEY).strip()
    if not key:
        return {
            "status":   "error",
            "provider": provider,
            "model":    model,
            "message":  f"{'GEMINI_API_KEY' if provider == 'gemini' else 'OPENAI_API_KEY'} "
                        "is not configured",
        }

    try:
        result = _call("You are a test assistant.", "Reply with the single word: OK")
        ok = len(result) > 0
        return {
            "status":   "ok" if ok else "unexpected_response",
            "provider": provider,
            "model":    model,
            "message":  "Connection successful" if ok else f"Unexpected: {result[:80]}",
        }
    except Exception as exc:
        safe_msg = str(exc)
        key_val = settings.GEMINI_API_KEY if provider == "gemini" else settings.OPENAI_API_KEY
        if key_val and key_val in safe_msg:
            safe_msg = safe_msg.replace(key_val, "[REDACTED]")
        return {
            "status":   "error",
            "provider": provider,
            "model":    model,
            "message":  safe_msg,
        }


# ── DB context builder ────────────────────────────────────────────────────

def _build_financial_context(db: Session) -> str:
    total_balance = db.query(func.sum(Account.current_balance)).scalar() or 0
    total_tx      = db.query(func.count(Transaction.id)).scalar() or 0
    reconciled    = db.query(func.count(Transaction.id)).filter(
                        Transaction.status == "reconciled").scalar() or 0
    unmatched     = db.query(func.count(Transaction.id)).filter(
                        Transaction.status == "unmatched").scalar() or 0
    disputed      = db.query(func.count(Transaction.id)).filter(
                        Transaction.status == "disputed").scalar() or 0
    recent = db.query(Transaction).order_by(
        Transaction.transaction_date.desc()).limit(5).all()

    ctx = {
        "total_cash_balance":  round(float(total_balance), 2),
        "total_transactions":  total_tx,
        "reconciled":          reconciled,
        "unmatched":           unmatched,
        "disputed":            disputed,
        "reconciliation_rate": round(reconciled / total_tx * 100, 1) if total_tx else 0,
        "recent_transactions": [
            {
                "id":          t.transaction_id,
                "date":        str(t.transaction_date),
                "description": t.description,
                "amount":      t.amount,
                "direction":   t.direction,
                "status":      t.status,
            }
            for t in recent
        ],
    }
    return json.dumps(ctx, indent=2)


# ── Public service functions ──────────────────────────────────────────────

def chat(db: Session, message: str) -> dict:
    context = _build_financial_context(db)
    system  = (
        "You are FinanceAI Assistant, an expert financial analyst. "
        "Answer questions using ONLY the financial data provided. "
        "Do not invent numbers or make up transactions. "
        "Be concise and professional. Format currency in INR (₹)."
    )
    user   = f"FINANCIAL DATA:\n{context}\n\nUSER QUESTION:\n{message}"
    answer = _call(system, user)
    return {"answer": answer, "data_used": json.loads(context)}


def settlement_query(db: Session, question: str) -> dict:
    unmatched_txs = db.query(Transaction).filter(
        Transaction.status.in_(["unmatched", "disputed"])
    ).limit(20).all()

    supporting = [
        {
            "id":          t.transaction_id,
            "date":        str(t.transaction_date),
            "description": t.description,
            "amount":      t.amount,
            "direction":   t.direction,
            "status":      t.status,
            "source":      t.source,
        }
        for t in unmatched_txs
    ]

    context = json.dumps(supporting, indent=2)
    system  = (
        "You are a settlement reconciliation expert. "
        "Answer questions about unmatched or disputed transactions using ONLY the data provided. "
        "Explain likely causes and suggest corrective actions."
    )
    user   = f"UNMATCHED/DISPUTED TRANSACTIONS:\n{context}\n\nQUESTION:\n{question}"
    answer = _call(system, user)

    return {
        "answer":                  answer,
        "supporting_transactions": supporting,
        "confidence":              0.85 if supporting else 0.4,
    }


def generate_insights(db: Session) -> list:
    context = _build_financial_context(db)
    ctx     = json.loads(context)

    insights: list[AIInsight] = []
    rate      = ctx["reconciliation_rate"]
    unmatched = ctx["unmatched"]
    balance   = ctx["total_cash_balance"]

    if rate < 90:
        insights.append(AIInsight(
            insight_type="reconciliation",
            title="Reconciliation Rate Below Target",
            description=(
                f"Current reconciliation rate is {rate}%, below the 90% threshold. "
                f"{unmatched} transactions remain unmatched."
            ),
            severity="warning",
        ))

    if unmatched > 20:
        insights.append(AIInsight(
            insight_type="unmatched",
            title=f"{unmatched} Unmatched Transactions Detected",
            description="High number of unmatched transactions. Review sources for missing settlement files.",
            severity="warning",
        ))

    if balance < 50000:
        insights.append(AIInsight(
            insight_type="cash_runway",
            title="Low Cash Balance Warning",
            description=f"Total cash balance is ₹{balance:,.0f}. Consider reviewing upcoming payables.",
            severity="critical",
        ))

    # AI-generated insight — use a short direct prompt to avoid timeouts
    system = (
        "You are a financial analyst. Reply with exactly one JSON object and nothing else. "
        "No markdown, no explanation, no code fences."
    )
    ai_prompt = (
        f"Given this financial summary: {json.dumps({'balance': balance, 'unmatched': unmatched, 'recon_rate': rate})}\n"
        'Write one insight as JSON: {"title":"...","description":"...","severity":"info"}'
    )
    try:
        raw   = _call(system, ai_prompt)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            ai_data = json.loads(match.group())
            insights.append(AIInsight(
                insight_type="ai_generated",
                title=ai_data.get("title", "AI Insight"),
                description=ai_data.get("description", raw[:300]),
                severity=ai_data.get("severity", "info"),
            ))
    except Exception:
        pass  # rule-based insights are still returned

    db.query(AIInsight).delete()
    for ins in insights:
        db.add(ins)
    db.commit()
    for ins in insights:
        db.refresh(ins)

    return insights
