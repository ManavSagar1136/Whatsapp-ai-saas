from fastapi import APIRouter
from backend.services.database_service import supabase, redis_client
from backend.services.llm_service import client as groq_client
import time

router = APIRouter(prefix="/health", tags=["System Verification"])

@router.get("/")
def health_check():
    """
    Comprehensive Startup System Health Ping.
    Tests Postgres, Redis, Groq, and Celery Queue Depth.
    """
    import os
    import psutil

    status = {
        "status": "operational",
        "timestamp": time.time(),
        "services": {
            "supabase": "disconnected",
            "redis": "disconnected",
            "groq_api": "disconnected",
            "celery_broker": "connected"
        },
        "metrics": {
            "queue_depth": 0,
            "cpu_usage_percent": psutil.cpu_percent(),
            "memory_usage_percent": psutil.virtual_memory().percent
        }
    }

    # 1. Check PostgreSQL Database (Supabase)
    if supabase:
        try:
             supabase.table('businesses').select('id').limit(1).execute()
             status["services"]["supabase"] = "connected"
        except Exception as e:
             status["services"]["supabase"] = f"error: {str(e)}"
             status["status"] = "degraded"

    # 2. Check Redis (Upstash) serving as Cache & Celery Broker
    try:
        redis_client.ping()
        status["services"]["redis"] = "connected"
        
        # Check Celery Queue Depth
        # Default celery queue name is 'celery'
        q_len = redis_client.llen("celery")
        status["metrics"]["queue_depth"] = q_len
        
        if q_len > 100:
            status["status"] = "warning"
            status["message"] = f"High queue depth: {q_len} tasks pending"
            
    except Exception as e:
        status["services"]["redis"] = f"error: {str(e)}"
        status["services"]["celery_broker"] = "offline"
        status["status"] = "degraded"

    # 3. Check Groq Inference API Reachability
    if groq_client:
         try:
              groq_client.models.list()
              status["services"]["groq_api"] = "connected"
         except Exception as e:
              status["services"]["groq_api"] = f"error: {str(e)}"
              status["status"] = "degraded"

    return status
