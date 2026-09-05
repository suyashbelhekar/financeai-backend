"""
Core API tests for FinanceAI backend.
Run: pytest tests/ -v  (from financeai/backend/)
"""


# ── Auth ──────────────────────────────────────────────────────────────────

def test_register(client):
    r = client.post("/api/auth/register", json={
        "name": "Alice", "email": "alice@test.com", "password": "password123"
    })
    assert r.status_code == 201
    assert "access_token" in r.json()


def test_register_duplicate_email(client):
    client.post("/api/auth/register", json={"name":"Bob","email":"bob@test.com","password":"pass1234"})
    r = client.post("/api/auth/register", json={"name":"Bob2","email":"bob@test.com","password":"pass1234"})
    assert r.status_code == 400


def test_login_success(client):
    client.post("/api/auth/register", json={"name":"Carol","email":"carol@test.com","password":"pass1234"})
    r = client.post("/api/auth/login", json={"email":"carol@test.com","password":"pass1234"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"name":"Dave","email":"dave@test.com","password":"pass1234"})
    r = client.post("/api/auth/login", json={"email":"dave@test.com","password":"wrongpass"})
    assert r.status_code == 401


def test_me(client, auth_headers):
    r = client.get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "test@test.com"


# ── Dashboard ─────────────────────────────────────────────────────────────

def test_dashboard_summary(client, auth_headers):
    r = client.get("/api/dashboard/summary", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_cash_balance" in data
    assert "reconciled_transactions" in data
    assert "unmatched_transactions" in data
    assert "recent_transactions" in data
    assert "ai_insights" in data


def test_cash_flow(client, auth_headers):
    r = client.get("/api/dashboard/cash-flow?period=12m", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Accounts ──────────────────────────────────────────────────────────────

def test_create_account(client, auth_headers):
    r = client.post("/api/accounts", headers=auth_headers, json={
        "account_name": "Test Account",
        "account_type": "Checking",
        "institution": "Test Bank",
        "currency": "INR",
        "current_balance": 10000.0
    })
    assert r.status_code == 201
    assert r.json()["account_name"] == "Test Account"


def test_list_accounts(client, auth_headers):
    r = client.get("/api/accounts", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_account(client, auth_headers):
    create = client.post("/api/accounts", headers=auth_headers, json={
        "account_name": "GetTest", "account_type": "Savings",
        "institution": "SBI", "currency": "INR", "current_balance": 5000
    })
    acc_id = create.json()["id"]
    r = client.get(f"/api/accounts/{acc_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["id"] == acc_id


# ── Transactions ──────────────────────────────────────────────────────────

def _create_account(client, headers):
    r = client.post("/api/accounts", headers=headers, json={
        "account_name": "TxAccount", "account_type": "Checking",
        "institution": "HDFC", "currency": "INR", "current_balance": 0
    })
    return r.json()["id"]


def test_create_transaction(client, auth_headers):
    acc_id = _create_account(client, auth_headers)
    r = client.post("/api/transactions", headers=auth_headers, json={
        "account_id": acc_id,
        "transaction_id": "TEST-TXN-001",
        "transaction_date": "2026-08-01",
        "description": "Test payment",
        "amount": 5000.0,
        "direction": "CREDIT",
        "currency": "INR",
        "source": "manual",
        "status": "pending"
    })
    assert r.status_code == 201
    assert r.json()["transaction_id"] == "TEST-TXN-001"


def test_list_transactions(client, auth_headers):
    r = client.get("/api/transactions", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "items" in data


def test_transaction_search(client, auth_headers):
    r = client.get("/api/transactions?search=Test", headers=auth_headers)
    assert r.status_code == 200


def test_duplicate_transaction(client, auth_headers):
    acc_id = _create_account(client, auth_headers)
    payload = {"account_id": acc_id, "transaction_id": "DUP-001",
               "transaction_date": "2026-08-01", "amount": 100.0,
               "direction": "CREDIT", "currency": "INR", "source": "manual", "status": "pending"}
    client.post("/api/transactions", headers=auth_headers, json=payload)
    r = client.post("/api/transactions", headers=auth_headers, json=payload)
    assert r.status_code == 409


# ── Reconciliation ────────────────────────────────────────────────────────

def test_reconciliation_run(client, auth_headers):
    r = client.post("/api/reconciliation/run", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_processed" in data
    assert "matched" in data
    assert "duration_seconds" in data


def test_reconciliation_results(client, auth_headers):
    r = client.get("/api/reconciliation/results", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Alerts ────────────────────────────────────────────────────────────────

def test_list_alerts(client, auth_headers):
    r = client.get("/api/alerts", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Forecasting ───────────────────────────────────────────────────────────

def test_generate_forecast(client, auth_headers):
    r = client.post("/api/forecast/generate", headers=auth_headers,
                    json={"periods": 3, "scenario": "base"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        assert "forecast" in data[0]
        assert "predicted_inflow" in data[0]


def test_get_forecast(client, auth_headers):
    r = client.get("/api/forecast?scenario=base", headers=auth_headers)
    assert r.status_code == 200


# ── Tax Matching ──────────────────────────────────────────────────────────

def test_tax_match_run(client, auth_headers):
    r = client.post("/api/tax/match", headers=auth_headers)
    assert r.status_code == 200
    assert "matched" in r.json()


def test_tax_results(client, auth_headers):
    r = client.get("/api/tax/results", headers=auth_headers)
    assert r.status_code == 200


# ── Settings ──────────────────────────────────────────────────────────────

def test_get_settings(client, auth_headers):
    r = client.get("/api/settings", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "currency" in data
    assert "forecast_period" in data


def test_update_settings(client, auth_headers):
    r = client.put("/api/settings", headers=auth_headers,
                   json={"currency": "USD", "forecast_period": 12})
    assert r.status_code == 200
    assert r.json()["currency"] == "USD"


# ── Health ────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
