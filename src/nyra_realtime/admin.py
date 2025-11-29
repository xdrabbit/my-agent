from fastapi import APIRouter, Header, HTTPException
from .config import settings
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger("nyra.admin")

def verify_admin(token: str | None):
    if not token or token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="invalid admin token")

class ModeRequest(BaseModel):
    mode: str

@router.post("/mode")
async def switch_mode(req: ModeRequest, x_admin_token: str | None = Header(None)):
    verify_admin(x_admin_token)
    # In the real implementation, this would notify session manager to change persona
    logger.info("Mode switch requested", extra={"mode": req.mode})
    return {"status":"ok","mode": req.mode}

@router.get("/status")
async def status(x_admin_token: str | None = Header(None)):
    verify_admin(x_admin_token)
    return {"status":"ok","app": settings.APP_NAME}
