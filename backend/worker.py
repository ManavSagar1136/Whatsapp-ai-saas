from celery import Celery
from backend.config import settings
from backend.utils.logging import get_logger
from backend.services.database_service import DatabaseService
from backend.services.whatsapp_service import WhatsAppService
from backend.services.state_manager import StateManager
import asyncio

logger = get_logger("celery_worker")

# Initialize Celery connected to Redis broker
celery_app = Celery("whatsapp_worker", broker=settings.redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True, 
    worker_prefetch_multiplier=1,
    # Reliability: Task Routing & Dead Letter Queue
    task_queues={
        "celery": {"exchange": "celery", "routing_key": "celery"},
        "dead_letter": {"exchange": "dead_letter", "routing_key": "dead_letter"},
    },
    task_default_queue="celery",
    task_routes={
        "process_msg": {"queue": "celery"},
    }
)

@celery_app.task(bind=True, max_retries=3, name="process_msg")
def process_message_task(self, phone_number_id: str, message: dict):
    """
    Background worker task to process incoming WhatsApp messages.
    Provides reliability, retry logic, and prevents webhook timeouts.
    """
    message_id = message.get("id")
    customer_phone = message.get("from")
    message_text = message.get("text", {}).get("body", "")
    
    logger.info(f"[Worker] Processing message {message_id} from {customer_phone}")
    
    startTime = time.time()
    try:
        # 1. Idempotency Check (prevent duplicate processing if Meta retries)
        if DatabaseService.is_message_processed(message_id):
            logger.info(f"[Worker] Message {message_id} already processed. Skipping.")
            return "skipped_duplicate"

        # 2. Get/Create Customer
        DatabaseService.get_or_create_customer(customer_phone)

        # 3. Save User Message
        DatabaseService.save_message(customer_phone, "user", message_text)

        # 4. Fetch Business Context with Redis Caching
        business_ctx = DatabaseService.get_business_cached(phone_number_id)
        if not business_ctx:
            logger.error(f"[Worker] No business found for receiving id: {phone_number_id}")
            return "failed_no_business"

        # 5. Intent, State Machine, and Groq LLM (Capture Metrics)
        start_llm = time.time()
        # StateManager now returns or passes forward metrics from LLMService
        response_text = StateManager.process_message(customer_phone, message_text, business_ctx)
        llm_duration = time.time() - start_llm

        # 6. Send Response
        loop = asyncio.get_event_loop()
        loop.run_until_complete(WhatsAppService.send_text_message(phone_number_id, customer_phone, response_text))
        loop.run_until_complete(WhatsAppService.mark_message_as_read(phone_number_id, message_id))

        # 7. Save Assistant Reply
        DatabaseService.save_message(customer_phone, "assistant", response_text)
        
        # 8. Mark Idempotency as Complete
        DatabaseService.mark_message_processed(message_id)
        
        total_duration = time.time() - startTime
        logger.info(f"[Worker] Message {message_id} successfully processed. [Total: {total_duration:.2f}s, LLM: {llm_duration:.2f}s]")
        return "success"
        
    except Exception as exc:
        logger.error(f"[Worker] Error processing {message_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
