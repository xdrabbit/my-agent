"""FastAPI entrypoint for Nyra Realtime Telephony (scaffold)

This file wires up the main API endpoints and includes a small demo mode.
"""
from fastapi import FastAPI
from .telephony import router as telephony_router
from .admin import router as admin_router
from .health import router as health_router

app = FastAPI(title="Nyra Realtime Telephony (scaffold)")

app.include_router(telephony_router, prefix="/telephony", tags=["telephony"])
app.include_router(admin_router, prefix="/control", tags=["control"])
app.include_router(health_router, prefix="/health", tags=["health"])

@app.get("/ready")
async def ready():
    return {"status": "ok"}
