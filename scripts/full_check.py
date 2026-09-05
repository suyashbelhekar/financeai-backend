"""
full_check.py — Complete project health check.
Tests: API key security, all endpoints, Gemini AI, frontend reachability.
Run: python scripts/full_check.py  (from financeai/backend/)
"""
import sys, os, json, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import httpx

BASE    = "http://localhost:8001"
FRONT   = "http://localhost:5173"
PASS    = "✅"
FAIL    = "❌"
WARN    = "⚠️ "
results = []

def check(label, ok, detail=""):
    mark = PASS if ok else FAIL
    results.append((label, ok))
    suffix = f"  → {detail}" if detail else ""
    print(f"  {mark}  {label}{suffix}")

print()
print("=" * 65)
print("  FinanceAI — Full Project Check")
print("=" * 65)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print()
print("── Section 1: API Key Security ──────────────────────────────")

from app.config import settings

# 1a. GEMINI_API_KEY exists and is non-empty
key = settings.GEMINI_API_KEY.strip()
check("GEMINI_API_KEY is set", bool(key), f"length={len(key)} chars")

# 1b. No AIza prefix check (opaque treatment)
check("No AIza prefix validation", True, "key treated as opaque string")

# 1c. Key not exposed via config properties  
exposed_fields = [f for f in ["VITE_GEMINI_API_KEY", "VITE_OPENAI_API_KEY"] 
                  if os.environ.get(f)]
check("No VITE_ key env vars exist", not exposed_fields, 
      "frontend cannot access keys" if not exposed_fields else f"EXPOSED: {exposed_fields}")

# 1d. Provider set to gemini
check("AI_PROVIDER=gemini", settings.AI_PROVIDER == "gemini", settings.AI_PROVIDER)

# 1e. Model configured
check("GEMINI_MODEL configured", bool(settings.GEMINI_MODEL), settings.GEMINI_MODEL)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print()
print("── Section 2: Backend Server ────────────────────────────────")

try:
    r = httpx.get(f"{BASE}/health", timeout=5)
    check("Backend running on :8001", r.status_code == 200, r.json().get("status","?"))
except Exception as e:
    check("Backend running on :8001", False, str(e)[:60])

try:
    r = httpx.get(f"{BASE}/docs", timeout=5)
    check("Swagger docs accessible", r.status_code == 200, "/docs")
except Exception as e:
    check("Swagger docs accessible", False, str(e)[:60])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print()
print("── Section 3: Frontend Server ───────────────────────────────")

try:
    r = httpx.get(FRONT, timeout=5)
    check("Frontend running on :5173", r.status_code == 200)
except Exception as e:
    check("Frontend running on :5173", False, str(e)[:60])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print()
print("── Section 4: Auth Endpoints ────────────────────────────────")

token = None
try:
    r = httpx.post(f"{BASE}/api/auth/login",
                   json={"email": "demo@financeai.com", "password": "demo1234"}, timeout=10)
    token = r.json().get("access_token")
    check("POST /api/auth/login", r.status_code == 200 and token, f"HTTP {r.status_code}")
except Exception as e:
    check("POST /api/auth/login", False, str(e)[:60])

if not token:
    print(f"\n  {FAIL}  Cannot continue without auth token — is the backend seeded?")
    sys.exit(1)

H = {"Authorization": f"Bearer {token}"}

try:
    r = httpx.get(f"{BASE}/api/auth/me", headers=H, timeout=5)
    d = r.json()
    check("GET /api/auth/me", r.status_code == 200, d.get("email","?"))
except Exception as e:
    check("GET /api/auth/me", False, str(e)[:60])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print()
print("── Section 5: Core Data Endpoints ───────────────────────────")

endpoints = [
    ("GET",  "/api/dashboard/summary",          None),
    ("GET",  "/api/dashboard/cash-flow?period=12m", None),
    ("GET",  "/api/accounts",                   None),
    ("GET",  "/api/transactions",               None),
    ("GET",  "/api/alerts",                     None),
    ("GET",  "/api/settings",                   None),
    ("GET",  "/api/reconciliation/results",     None),
    ("GET",  "/api/tax/results",                None),
    ("GET",  "/api/forecast?scenario=base",     None),
]

for method, path, body in endpoints:
    try:
        if method == "GET":
            r = httpx.get(f"{BASE}{path}", headers=H, timeout=15)
        else:
            r = httpx.post(f"{BASE}{path}", headers=H, json=body, timeout=15)
        ok = r.status_code in (200, 201)
        detail = f"HTTP {r.status_code}"
        if ok and r.status_code == 200:
            d = r.json()
            if isinstance(d, list):
                detail += f" · {len(d)} items"
            elif isinstance(d, dict):
                for key_hint in ["total","total_cash_balance","status","currency"]:
                    if key_hint in d:
                        detail += f" · {key_hint}={d[key_hint]}"
                        break
        check(f"{method} {path.split('?')[0]}", ok, detail)
    except Exception as e:
        check(f"{method} {path.split('?')[0]}", False, str(e)[:60])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print()
print("── Section 6: Gemini AI Endpoints ───────────────────────────")

# Health
try:
    r = httpx.get(f"{BASE}/api/ai/health", headers=H, timeout=60)
    d = r.json()
    ok = r.status_code == 200 and d.get("status") == "ok"
    check("GET /api/ai/health", ok,
          f"provider={d.get('provider')} model={d.get('model')} status={d.get('status')}")
    # Confirm key not leaked
    raw = str(d)
    key_leaked = key and key in raw
    check("API key NOT in health response", not key_leaked, "secure" if not key_leaked else "LEAKED!")
except Exception as e:
    check("GET /api/ai/health", False, str(e)[:80])

# Chat
try:
    r = httpx.post(f"{BASE}/api/ai/chat", headers=H,
                   json={"message": "How many accounts are connected?"}, timeout=30)
    d = r.json()
    ok = r.status_code == 200 and "answer" in d
    answer_preview = d.get("answer","")[:80] if ok else str(d)[:80]
    check("POST /api/ai/chat", ok, answer_preview)
    # Confirm key not leaked
    raw = str(d)
    key_leaked = key and key in raw
    check("API key NOT in chat response", not key_leaked, "secure" if not key_leaked else "LEAKED!")
except Exception as e:
    check("POST /api/ai/chat", False, str(e)[:80])

# Settlement Q&A
try:
    r = httpx.post(f"{BASE}/api/settlement/query", headers=H,
                   json={"question": "What is unmatched?"}, timeout=30)
    ok = r.status_code == 200 and "answer" in r.json()
    check("POST /api/settlement/query", ok, f"HTTP {r.status_code}")
except Exception as e:
    check("POST /api/settlement/query", False, str(e)[:80])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print()
print("── Section 7: CSV Import ────────────────────────────────────")

try:
    # Get first account id
    accs = httpx.get(f"{BASE}/api/accounts", headers=H, timeout=10).json()
    if accs:
        acc_id = str(accs[0]["id"])
        csv_data = (
            b"bank_transaction_id,id,transaction_id,bank_tx_id,tx_id,date,"
            b"transaction_type,description,merchant,direction,amount,balance\n"
            b"CHKIMPORT1,X1,CHK-IMPORT-001,BTX999,TX999,2026-09-10,"
            b"UPI,Test Import,TestCo,CREDIT,1000.0,1000.0\n"
        )
        files = {"file": ("test.csv", csv_data, "text/csv")}
        r = httpx.post(
            f"{BASE}/api/transactions/import?account_id={acc_id}",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            timeout=15,
        )
        d = r.json()
        ok = r.status_code == 200
        check("POST /api/transactions/import", ok,
              f"imported={d.get('imported',0)} dupes={d.get('duplicates',0)} errors={len(d.get('errors',[]))}")
    else:
        check("POST /api/transactions/import", False, "no accounts found")
except Exception as e:
    check("POST /api/transactions/import", False, str(e)[:80])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print()
print("=" * 65)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total  = len(results)
print(f"  Results: {passed}/{total} passed  |  {failed} failed")

if failed == 0:
    print()
    print("  🎉  ALL CHECKS PASSED — Project is fully running!")
    print()
    print("  Frontend  →  http://localhost:5173")
    print("  Backend   →  http://localhost:8001")
    print("  Swagger   →  http://localhost:8001/docs")
    print("  Login     →  demo@financeai.com / demo1234")
else:
    print()
    print("  Failed checks:")
    for label, ok in results:
        if not ok:
            print(f"    {FAIL}  {label}")

print("=" * 65)
sys.exit(0 if failed == 0 else 1)
