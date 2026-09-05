from datetime import date
from typing import Optional
import re


def normalize_amount(value) -> Optional[float]:
    """Convert any amount representation to float."""
    if value is None:
        return None
    try:
        cleaned = str(value).replace(",", "").replace("₹", "").replace("$", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def normalize_date(value) -> Optional[date]:
    """Parse multiple date formats into a date object."""
    if value is None:
        return None
    import pandas as pd
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y",
        "%Y/%m/%d", "%d-%b-%Y", "%b %d, %Y",
    ]
    for fmt in formats:
        try:
            return pd.to_datetime(str(value), format=fmt).date()
        except Exception:
            continue
    try:
        return pd.to_datetime(str(value), dayfirst=True).date()
    except Exception:
        return None


def is_valid_direction(value: str) -> bool:
    return str(value).upper() in {"CREDIT", "DEBIT"}


def sanitize_string(value, max_len: int = 500) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    # Remove SQL injection patterns
    cleaned = re.sub(r"[;'\"\\]", "", cleaned)
    return cleaned[:max_len] if cleaned else None


REQUIRED_BANK_COLS = {"transaction_id", "date", "direction", "amount"}
REQUIRED_PROCESSOR_COLS = {"settlement_id", "transaction_id", "settlement_date",
                           "gross_amount", "net_amount", "status"}


def validate_csv_columns(df_cols: set, required: set) -> list:
    missing = required - {c.lower().strip() for c in df_cols}
    return list(missing)
