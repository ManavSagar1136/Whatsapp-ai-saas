from fastapi import FastAPI
from backend.routes import webhook, api
from backend.utils.logging import get_logger, setup_logs_directory
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from backend.config import settings

setup_logs_directory()
logger = get_logger("main")

# Sentry Monitoring Initialization
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    logger.info("Sentry monitoring initialized.")

app = FastAPI(
    title="WhatsApp AI SaaS Platform",
    description="Production-ready multi-tenant AI booking assistant.",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(api.router)
app.include_router(analytics.router)
app.include_router(health.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up WhatsApp AI Platform (Phase 3 Hardened)...")

@app.get("/")
async def health_check():
    return {"status": "ok", "iteration": 1, "version": "SaaS Platform 3.0"}
