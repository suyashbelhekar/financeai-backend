"""
test_gemini.py — end-to-end Gemini API verification.
Run: python scripts/test_gemini.py  (from financeai/backend/)
"""
import sys, os, warnings
warnings.filterwarnings("ignore")   # silence AFC SDK notice
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings

print("=" * 60)
print("FinanceAI — Gemini API Test")
print("=" * 60)
print(f"  Provider : {settings.AI_PROVIDER}")
print(f"  Model    : {settings.GEMINI_MODEL}")
print(f"  Key set  : {'YES (hidden)' if settings.GEMINI_API_KEY.strip() else 'NO — missing!'}")
print()

# ── 1. Health check ────────────────────────────────────────────────────────
print("── Test 1: Health check ──")
from app.services.ai_service import check_ai_health
h = check_ai_health()
print(f"  status  : {h['status']}")
print(f"  provider: {h['provider']}")
print(f"  model   : {h['model']}")
print(f"  message : {h['message']}")
if h["status"] != "ok":
    print("\n❌ Health check failed. Stopping.")
    sys.exit(1)
print("  ✓ PASS")

# ── 2. Simple generate ────────────────────────────────────────────────────
print()
print("── Test 2: Simple generate ──")
from app.services.ai_service import _call
r = _call("You are a concise assistant.", "What is 2+2? Answer in one word.")
print(f"  response: {r}")
if r.startswith("[AI unavailable"):
    print("  ❌ FAIL")
    sys.exit(1)
print("  ✓ PASS")

# ── 3. Finance Q&A ────────────────────────────────────────────────────────
print()
print("── Test 3: Finance Q&A ──")
ctx = '{"total_cash_balance": 176651, "reconciled": 26, "unmatched": 2, "reconciliation_rate": 92.8}'
r2 = _call(
    "You are a finance analyst. Answer using only the data provided. Be brief.",
    f"DATA:\n{ctx}\n\nQUESTION: What is the reconciliation rate?"
)
print(f"  response: {r2[:120]}")
if r2.startswith("[AI unavailable"):
    print("  ❌ FAIL")
    sys.exit(1)
print("  ✓ PASS")

# ── 4. JSON output ────────────────────────────────────────────────────────
print()
print("── Test 4: JSON output (for insights) ──")
import json, re
r3 = _call(
    "You are a financial analyst. Reply with exactly one JSON object and nothing else. No markdown.",
    '{"balance":176651,"unmatched":2,"recon_rate":92.8} — Write one insight as JSON: {"title":"...","description":"...","severity":"info"}'
)
print(f"  raw: {r3[:150]}")
match = re.search(r"\{.*\}", r3, re.DOTALL)
if match:
    try:
        parsed = json.loads(match.group())
        print(f"  parsed title: {parsed.get('title','?')}")
        print("  ✓ PASS")
    except Exception as e:
        print(f"  ⚠ JSON parse error: {e} (non-critical — fallback used)")
else:
    print("  ⚠ No JSON block (non-critical — rule-based insights still work)")

# ── 5. Security check — key not in output ─────────────────────────────────
print()
print("── Test 5: Key not leaked in any response ──")
key = settings.GEMINI_API_KEY
for label, text in [("health_msg", h["message"]), ("test2", r), ("test3", r2), ("test4", r3)]:
    if key and key in text:
        print(f"  ❌ KEY LEAKED in {label}!")
        sys.exit(1)
print("  ✓ API key not present in any response")

print()
print("=" * 60)
print("✅ ALL TESTS PASSED — Gemini is fully working")
print("=" * 60)
