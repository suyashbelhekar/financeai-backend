"""
csv_processor.py
Handles CSV ingestion for bank statements and processor settlements.
Validates, normalises, deduplicates then returns clean records + error log.
"""
from __future__ import annotations
import io
from typing import Tuple, List, Dict, Any

import pandas as pd

from app.utils.validators import (
    normalize_amount, normalize_date, is_valid_direction,
    sanitize_string, validate_csv_columns, REQUIRED_BANK_COLS,
)

MAX_CSV_SIZE_BYTES = 10 * 1024 * 1024   # 10 MB


def process_bank_csv(
    content: bytes,
    account_id: str,
) -> Tuple[List[Dict[str, Any]], List[str], int, int]:
    """
    Returns: (clean_records, error_messages, duplicate_count, rejected_count)
    """
    if len(content) > MAX_CSV_SIZE_BYTES:
        return [], ["File exceeds 10 MB limit"], 0, 0

    try:
        df = pd.read_csv(io.BytesIO(content), dtype=str)
    except Exception as e:
        return [], [f"Could not parse CSV: {e}"], 0, 0

    df.columns = [c.lower().strip() for c in df.columns]

    # Accept common column aliases
    col_aliases = {
        "bank_transaction_id": "transaction_id",
        "tx_id": "transaction_id",
        "txn_id": "transaction_id",
        "transaction_date": "date",
        "debit_credit": "direction",
        "credit_debit": "direction",
    }
    df.rename(columns=col_aliases, inplace=True)

    missing = validate_csv_columns(set(df.columns), REQUIRED_BANK_COLS)
    if missing:
        return [], [f"Missing required columns: {missing}"], 0, len(df)

    errors: List[str] = []
    records: List[Dict[str, Any]] = []
    seen_ids: set = set()
    duplicate_count = 0
    rejected_count = 0

    for idx, row in df.iterrows():
        row_num = idx + 2   # 1-indexed, header = row 1

        tx_id = sanitize_string(row.get("transaction_id"), 100)
        if not tx_id:
            errors.append(f"Row {row_num}: missing transaction_id")
            rejected_count += 1
            continue

        if tx_id in seen_ids:
            duplicate_count += 1
            continue
        seen_ids.add(tx_id)

        tx_date = normalize_date(row.get("date"))
        if not tx_date:
            errors.append(f"Row {row_num}: invalid date '{row.get('date')}'")
            rejected_count += 1
            continue

        amount = normalize_amount(row.get("amount"))
        if amount is None or amount < 0:
            errors.append(f"Row {row_num}: invalid amount '{row.get('amount')}'")
            rejected_count += 1
            continue

        direction = str(row.get("direction", "")).upper().strip()
        if not is_valid_direction(direction):
            errors.append(f"Row {row_num}: direction must be CREDIT or DEBIT, got '{direction}'")
            rejected_count += 1
            continue

        records.append({
            "account_id": account_id,
            "transaction_id": tx_id,
            "transaction_date": tx_date,
            "description": sanitize_string(row.get("description")),
            "merchant": sanitize_string(row.get("merchant"), 200),
            "amount": amount,
            "direction": direction,
            "transaction_type": sanitize_string(row.get("transaction_type", row.get("type")), 50),
            "currency": sanitize_string(row.get("currency", "INR"), 10) or "INR",
            "balance_after": normalize_amount(row.get("balance")),
            "source": "bank_csv",
            "status": "pending",
        })

    return records, errors, duplicate_count, rejected_count
