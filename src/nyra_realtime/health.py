from fastapi import APIRouter
from .config import settings

router = APIRouter()

@router.get("/ping")
async def ping():
    return {"status": "ok", "app": settings.APP_NAME}
