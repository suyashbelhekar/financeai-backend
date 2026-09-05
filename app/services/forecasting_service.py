"""
forecasting_service.py – Linear regression + moving-average cash forecasting.
No heavy ML dependencies; uses sklearn LinearRegression over historical monthly data.
"""
from __future__ import annotations
import numpy as np
from datetime import date, timedelta
from calendar import month_abbr
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.transaction import Transaction
from app.models.forecast import Forecast


def _get_monthly_history(db: Session) -> List[dict]:
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
    monthly: dict = {}
    for r in rows:
        key = (int(r.yr), int(r.mo))
        if key not in monthly:
            monthly[key] = {"inflow": 0.0, "outflow": 0.0}
        if r.direction == "CREDIT":
            monthly[key]["inflow"] += float(r.total)
        else:
            monthly[key]["outflow"] += float(r.total)
    return [{"yr": k[0], "mo": k[1], **v} for k in sorted(monthly) for v in [monthly[k]]]


def _linear_forecast(values: List[float], periods: int) -> List[float]:
    if len(values) < 2:
        last = values[-1] if values else 0.0
        return [last] * periods

    from sklearn.linear_model import LinearRegression
    X = np.arange(len(values)).reshape(-1, 1)
    y = np.array(values)
    model = LinearRegression().fit(X, y)
    future_X = np.arange(len(values), len(values) + periods).reshape(-1, 1)
    return [max(0.0, float(v)) for v in model.predict(future_X)]


def _confidence(n_samples: int) -> float:
    """More history → higher confidence, capped at 92%."""
    return round(min(0.92, 0.5 + n_samples * 0.04), 2)


SCENARIO_MULTIPLIERS = {
    "base": (1.0, 1.0),
    "bull": (1.18, 0.92),
    "bear": (0.85, 1.10),
}


def generate_forecast(db: Session, periods: int = 6, scenario: str = "base") -> List[dict]:
    history = _get_monthly_history(db)
    inflows  = [h["inflow"]  for h in history]
    outflows = [h["outflow"] for h in history]

    inflow_fc  = _linear_forecast(inflows,  periods)
    outflow_fc = _linear_forecast(outflows, periods)

    in_mult, out_mult = SCENARIO_MULTIPLIERS.get(scenario, (1.0, 1.0))
    conf = _confidence(len(history))

    # Starting balance = last known balance
    from app.models.account import Account
    last_balance = db.query(func.sum(Account.current_balance)).scalar() or 0.0

    results = []
    balance = last_balance
    today = date.today()

    # Delete old forecasts for this scenario
    db.query(Forecast).filter(Forecast.scenario == scenario).delete()

    for i in range(periods):
        # Forecast month
        months_ahead = i + 1
        target = date(today.year + (today.month + months_ahead - 1) // 12,
                      (today.month + months_ahead - 1) % 12 + 1, 1)

        predicted_in  = round(inflow_fc[i]  * in_mult,  2)
        predicted_out = round(outflow_fc[i] * out_mult, 2)
        balance = round(balance + predicted_in - predicted_out, 2)

        fc = Forecast(
            forecast_date=target,
            predicted_inflow=predicted_in,
            predicted_outflow=predicted_out,
            predicted_balance=balance,
            confidence=conf,
            model_version="linear_v1",
            scenario=scenario,
        )
        db.add(fc)

        results.append({
            "month": f"{month_abbr[target.month]} {str(target.year)[2:]}",
            "forecast_date": str(target),
            "forecast": predicted_in,
            "low": round(predicted_in * 0.88, 2),
            "high": round(predicted_in * 1.12, 2),
            "predicted_inflow": predicted_in,
            "predicted_outflow": predicted_out,
            "predicted_balance": balance,
            "confidence": conf,
            "scenario": scenario,
        })

    db.commit()
    return results
