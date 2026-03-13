from fastapi import APIRouter, Request, Query, HTTPException, Header
from backend.models.schemas import WhatsAppWebhookPayload
from backend.utils.logging import get_logger
from backend.config import settings
from backend.worker import celery_app
import hmac
import hashlib
import json
import redis
import time

logger = get_logger("webhook_router")
router = APIRouter(prefix="/webhook", tags=["Webhook"])

WHATSAPP_VERIFY_TOKEN = settings.whatsapp_verify_token
APP_SECRET = settings.whatsapp_app_secret

# Initialize rate limit redis connection
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

def verify_meta_signature(payload_body: bytes, signature_header: str):
    """Validates X-Hub-Signature-256 from Meta."""
    if not signature_header or not signature_header.startswith("sha256="):
        logger.warning("Missing or malformed X-Hub-Signature-256 header.")
        raise HTTPException(status_code=403, detail="Invalid signature")

    expected_hash = hmac.new(
        key=APP_SECRET.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    signature = signature_header.split("sha256=")[1]
    
    if not hmac.compare_digest(expected_hash, signature):
        logger.error("Webhook signature mismatch detected. Possible spoofing attack.")
        raise HTTPException(status_code=403, detail="Signature mismatch")

def check_rate_limit(phone_number: str):
    """Redis sliding window rate limiting (max 20 messages per minute)."""
    current_time = int(time.time())
    window_start = current_time - 60
    key = f"rate_limit:{phone_number}"
    
    # Clean up old timestamps
    redis_client.zremrangebyscore(key, 0, window_start)
    
    # Count messages in the last 60 seconds
    msg_count = redis_client.zcard(key)
    
    if msg_count >= 20:
        logger.warning(f"Rate limit exceeded for {phone_number}")
        raise HTTPException(status_code=429, detail="Too Many Requests")
        
    # Add current timestamp
    redis_client.zadd(key, {str(current_time): current_time})
    redis_client.expire(key, 60)

from fastapi.responses import PlainTextResponse

@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Meta Webhook Registration Endpoint."""
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully.")
        return PlainTextResponse(content=hub_challenge)
    logger.warning(f"Failed webhook verification: token mismatch or bad mode: {hub_mode}")
    raise HTTPException(status_code=403, detail="Invalid verify token")


@router.post("")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None)
):
    """
    Receives incoming WhatsApp messages.
    Validates signature, rate limits, and OFF-LOADS to Celery instantly.
    """
    body_bytes = await request.body()
    
    # 1. Signature Verification for Security
    # In live prod, ensure APP_SECRET is set, else skip for local tests if needed.
    if APP_SECRET and APP_SECRET != "mock-app-secret":
        verify_meta_signature(body_bytes, x_hub_signature_256)

    try:
        payload_data = json.loads(body_bytes)
        payload = WhatsAppWebhookPayload(**payload_data)
        
        for entry in payload.entry:
            for change in entry.changes:
                if change.value.messages:
                    phone_number_id = change.value.metadata.phone_number_id
                    for message in change.value.messages:
                        sender_phone = message.from_
                        msg_dict = message.model_dump()
                        
                        # 2. Rate Limiting per aggressive user
                        check_rate_limit(sender_phone)
                        
                        # 3. Offload to Celery Queue instead of BackgroundTasks
                        celery_app.send_task("process_msg", kwargs={
                            "phone_number_id": phone_number_id,
                            "message": msg_dict
                        })
                        logger.debug(f"Queued message from {sender_phone} to Celery.")
                        
        # 4. Return 200 immediately so Meta doesn't drop the webhook
        return {"status": "ok"}
        
    except json.JSONDecodeError:
        logger.error("Failed to parse Meta JSON.")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return {"status": "error"}
