"""Verify demo data via live API."""
import sys, os, json, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import httpx

BASE = "http://localhost:8001"
r = httpx.post(f"{BASE}/api/auth/login",
               json={"email": "demo@financeai.com", "password": "demo1234"}, timeout=10)
h = {"Authorization": "Bearer " + r.json()["access_token"]}

s = httpx.get(f"{BASE}/api/dashboard/summary", headers=h, timeout=15).json()
print("=== DASHBOARD ===")
print(f"  Total balance : INR {s['total_cash_balance']:,.0f}")
print(f"  Reconciled    : {s['reconciled_transactions']}")
print(f"  Unmatched     : {s['unmatched_transactions']}")
print(f"  Recon rate    : {s['reconciliation_rate']}%")
print(f"  AI insights   : {len(s['ai_insights'])}")
print(f"  Recent txns   : {len(s['recent_transactions'])}")

print()
print("=== TRANSACTIONS ===")
for t in s["recent_transactions"]:
    print(f"  {t['transaction_id']}  {t['direction']}  {t['amount']}  [{t['status']}]  {t['description']}")

print()
print("=== ACCOUNTS ===")
for a in httpx.get(f"{BASE}/api/accounts", headers=h, timeout=10).json():
    print(f"  {a['account_name']} ({a['institution']})  INR {a['current_balance']:,.0f}  [{a['status']}]")

print()
print("=== ALERTS ===")
for a in httpx.get(f"{BASE}/api/alerts", headers=h, timeout=10).json():
    print(f"  [{a['severity'].upper()}] {a['title']}")

print()
print("=== FORECAST ===")
for f in httpx.get(f"{BASE}/api/forecast?scenario=base", headers=h, timeout=10).json():
    print(f"  {f['month']}  inflow={f['predicted_inflow']:,.0f}  balance={f['predicted_balance']:,.0f}  conf={int(f['confidence']*100)}%")

print()
print("=== AI INSIGHTS ===")
for i in httpx.get(f"{BASE}/api/ai/insights", headers=h, timeout=15).json():
    print(f"  [{i['severity'].upper()}] {i['title']}")

print()
print("=== TAX MATCHES ===")
for t in httpx.get(f"{BASE}/api/tax/results", headers=h, timeout=10).json():
    print(f"  {t['tax_category']}  code={t['tax_code']}  conf={int(t['confidence']*100)}%  [{t['status']}]")

print()
print("All demo data verified.")
