"""
FinanceAI – FastAPI Application Entry Point
Run: uvicorn app.main:app --reload --port 8001
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.database import create_tables

# Routers
from app.routers import (
    auth, dashboard, accounts, transactions,
    reconciliation, settlement, forecasting,
    tax_matching, ai_assistant, alerts, settings as settings_router
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables...")
    create_tables()
    logger.info("FinanceAI API ready.")
    yield


app = FastAPI(
    title="FinanceAI API",
    description="AI-powered finance automation platform backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global error handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error",
                 "error_code": "INTERNAL_ERROR"},
    )

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(reconciliation.router)
app.include_router(settlement.router)
app.include_router(forecasting.router)
app.include_router(tax_matching.router)
app.include_router(ai_assistant.router)
app.include_router(alerts.router)
app.include_router(settings_router.router)

# ── Health check ──────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "FinanceAI API", "version": "1.0.0"}
