import json
from supabase import create_client, Client
from backend.config import settings
from backend.utils.logging import get_logger
from typing import Dict, Any, List, Optional
import os
import redis
from tenacity import retry, wait_exponential, stop_after_attempt
import httpx

logger = get_logger("database_service")

supabase_url = os.environ.get("SUPABASE_URL", settings.supabase_url)
supabase_key = os.environ.get("SUPABASE_KEY", settings.supabase_key)
supabase = create_client(supabase_url, supabase_key) if supabase_url and supabase_url != "mock-url" else None

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

class DatabaseService:
    # --- Idempotency Logic ---
    @staticmethod
    def is_message_processed(message_id: str) -> bool:
        """Checks if a WhatsApp message ID has already been processed to avoid double-actions."""
        if not supabase: return False
        try:
            res = supabase.table('processed_messages').select('message_id').eq('message_id', message_id).execute()
            return len(res.data) > 0
        except Exception as e:
            logger.error(f"Idempotency check error: {e}")
            return False

    @staticmethod
    def mark_message_processed(message_id: str):
        if not supabase: return
        try:
            supabase.table('processed_messages').insert({"message_id": message_id}).execute()
        except Exception as e:
            logger.error(f"Failed to mark message processed: {e}")

    # --- Caching Business Context ---
    @staticmethod
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3)
    )
    def get_business_cached(phone_number_id: str) -> Optional[Dict]:
        """Fetches business context, hitting Redis Cache first. Falls back to PG."""
        cache_key = f"business_ctx:{phone_number_id}"
        
        # 1. Check Redis
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT for {phone_number_id}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis cache read error: {e}")

        # 2. Cache Miss -> Query Supabase
        logger.debug(f"Cache MISS for {phone_number_id}, falling back to PostgreSQL.")
        if not supabase: return None
        try:
            # Join with the new relational business_services table
            res = supabase.table('businesses').select('*, business_services(service_name, duration_minutes, price)').eq('whatsapp_number_id', phone_number_id).execute()
            if not res.data:
                return None
            
            business_data = res.data[0]
            # Map relation to expected key for LLM context
            if "business_services" in business_data:
                business_data["services_offered"] = business_data.pop("business_services")
            
            # 3. Save to Redis with 24 Hour TTL
            try:
                redis_client.setex(cache_key, 86400, json.dumps(business_data))
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")
                
            return business_data
            
        except Exception as e:
            logger.error(f"Error fetching business {phone_number_id}: {e}")
            return None

    # --- Core DB Functions (Existing) ---
    @staticmethod
    def get_customer(phone_number: str) -> Optional[Dict]:
        if not supabase: return None
        res = supabase.table('customers').select('*').eq('phone_number', phone_number).execute()
        return res.data[0] if res.data else None

    @staticmethod
    def create_customer(phone_number: str, name: str = "Unknown") -> Dict:
        if not supabase: return {"phone_number": phone_number, "name": name}
        try:
            new_cust = supabase.table('customers').insert({"phone_number": phone_number, "name": name}).execute()
            return new_cust.data[0]
        except:
            return {"phone_number": phone_number}

    @staticmethod
    def get_or_create_customer(phone_number: str):
        cust = DatabaseService.get_customer(phone_number)
        if not cust:
            return DatabaseService.create_customer(phone_number)
        return cust

    @staticmethod
    def save_message(phone_number: str, role: str, content: str):
        if not supabase: return
        supabase.table('chat_history').insert({"customer_phone": phone_number, "role": role, "message_content": content}).execute()

    @staticmethod
    def get_chat_history(phone_number: str, limit: int = 10) -> List[Dict]:
        if not supabase: return []
        res = supabase.table('chat_history').select('role, message_content').eq('customer_phone', phone_number).order('created_at', desc=True).limit(limit).execute()
        return list(reversed(res.data))

    @staticmethod
    def get_conversation_state(phone_number: str) -> Dict:
        if not supabase: return {"current_state": "INIT", "booking_context": {}}
        res = supabase.table('conversation_state').select('*').eq('customer_phone', phone_number).execute()
        if res.data: return res.data[0]
        new_state = supabase.table('conversation_state').insert({"customer_phone": phone_number, "current_state": "INIT", "booking_context": {}}).execute()
        return new_state.data[0]

    @staticmethod
    def update_conversation_state(phone_number: str, state: str, context: dict):
        if not supabase: return
        supabase.table('conversation_state').update({"current_state": state, "booking_context": context, "last_updated": "now()"}).eq('customer_phone', phone_number).execute()

    @staticmethod
    def get_appointments_by_date(business_id: str, date_str: str) -> List[Dict]:
        if not supabase: return []
        start_date = f"{date_str}T00:00:00"
        end_date = f"{date_str}T23:59:59"
        res = supabase.table('appointments').select('*').eq('business_id', business_id).gte('start_time', start_date).lte('start_time', end_date).eq('status', 'CONFIRMED').execute()
        return res.data

    @staticmethod
    def create_appointment(business_id: str, customer_phone: str, service_type: str, start_time: str, end_time: str) -> bool:
        if not supabase: return True
        try:
            supabase.table('appointments').insert({
                "business_id": business_id, "customer_phone": customer_phone,
                "service_type": service_type, "start_time": start_time,
                "end_time": end_time, "status": "CONFIRMED"
            }).execute()
            return True
        except:
            return False

    @staticmethod
    def save_usage_metrics(business_id: str, message_id: str, tokens: int, latency: float, intent: str):
        """Persists granular usage and performance data for SaaS analytics."""
        if not supabase: return
        try:
            supabase.table('usage_logs').insert({
                "business_id": business_id,
                "message_id": message_id,
                "tokens_used": tokens,
                "latency_seconds": latency,
                "intent_detected": intent
            }).execute()
        except Exception as e:
            logger.error(f"Failed to save usage metrics: {e}")
