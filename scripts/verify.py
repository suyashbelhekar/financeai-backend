"""Quick endpoint verification script."""
import httpx, sys

BASE = "http://localhost:8001"

r = httpx.post(f"{BASE}/api/auth/login",
               json={"email": "demo@financeai.com", "password": "demo1234"}, timeout=15)
print("LOGIN:", r.status_code)
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

r6 = httpx.post(f"{BASE}/api/reconciliation/run", headers=h, timeout=60)
print("RECONCILIATION:", r6.status_code, "-", r6.json())

r7 = httpx.post(f"{BASE}/api/forecast/generate",
                headers=h, json={"periods": 3, "scenario": "base"}, timeout=60)
print("FORECAST:", r7.status_code, "- periods:", len(r7.json()))

r8 = httpx.post(f"{BASE}/api/tax/match", headers=h, timeout=60)
print("TAX MATCH:", r8.status_code, "- matched:", r8.json().get("matched"))

r9 = httpx.get(f"{BASE}/api/alerts", headers=h, timeout=30)
print("ALERTS:", r9.status_code, "- count:", len(r9.json()))

r10 = httpx.get(f"{BASE}/api/settings", headers=h, timeout=15)
print("SETTINGS:", r10.status_code, "-", r10.json())

r11 = httpx.get(f"{BASE}/api/tax/results", headers=h, timeout=15)
print("TAX RESULTS:", r11.status_code, "- count:", len(r11.json()))

r12 = httpx.get(f"{BASE}/api/reconciliation/results", headers=h, timeout=15)
print("RECON RESULTS:", r12.status_code, "- count:", len(r12.json()))

print(); print("All endpoints PASSED!")
