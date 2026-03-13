import httpx
import os
from backend.utils.logging import get_logger
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = get_logger("whatsapp_service")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")

class WhatsAppService:
    @staticmethod
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException))
    )
    async def send_text_message(phone_number_id: str, to: str, text: str):
        """Send a plain text message via Meta WhatsApp Cloud API with automatic retries."""
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }
        
        logger.debug(f"Sending message to {to}: {text[:50]}...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=5.0)
                response.raise_for_status()
                logger.info(f"Message sent successfully to {to}")
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"WhatsApp API Error {e.response.status_code}: {e.response.text}")
                raise # Let tenacity retry
            except Exception as e:
                logger.error(f"Failed to send message to {to}: {e}")
                raise

    @staticmethod
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException))
    )
    async def mark_message_as_read(phone_number_id: str, message_id: str):
        """Mark an incoming message as read status with auto-retries."""
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=5.0)
                response.raise_for_status()
            except Exception as e:
                logger.warning(f"Failed to mark message {message_id} as read: {e}")
                raise
