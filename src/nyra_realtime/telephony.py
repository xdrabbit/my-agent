from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from .config import settings
import logging

router = APIRouter()
logger = logging.getLogger("nyra.telephony")

class TwilioWebhook(BaseModel):
    call_sid: str
    account_sid: str | None = None
    direction: str | None = None
    from_phone: str | None = None
    to_phone: str | None = None
    media_stream_id: str | None = None

@router.post("/webhook")
async def twilio_webhook(body: TwilioWebhook):
    """Twilio will call this webhook to notify of an inbound call or event.

    This stub accepts a Twilio-like JSON payload and returns a placeholder response. It should be replaced with full Twilio
    webhook verification and Media Streams handshake.
    """
    logger.info("Received Twilio webhook event", extra={"call_sid": body.call_sid, "direction": body.direction})
    # TODO: verify Twilio signature (X-Twilio-Signature header)

    # Minimum allowed operations for now
    return {"status": "accepted", "call_sid": body.call_sid}

class OutboundRequest(BaseModel):
    to: str
    from_phone: str
    twiml_url: str | None = None

@router.post("/call/outbound")
async def create_outbound(req: OutboundRequest):
    """Initiate an outbound call via Twilio API (stub).

    This will return a mocked call ID. Executor agent should replace with live Twilio REST integration.
    """
    if not settings.TWILIO_ACCOUNT_SID:
        raise HTTPException(status_code=503, detail="Twilio not configured")

    # TODO: call Twilio REST API to create call and attach Media Stream
    fake_call_sid = "CALL-FAKE-12345"
    logger.info("Initiated outbound call", extra={"to": req.to, "from": req.from_phone})
    return {"call_sid": fake_call_sid, "status":"initiated"}
