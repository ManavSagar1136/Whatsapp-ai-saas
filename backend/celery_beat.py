from backend.worker import celery_app
from celery.schedules import crontab
from backend.services.database_service import supabase
from backend.utils.logging import get_logger
from datetime import datetime, timedelta

logger = get_logger("celery_beat")

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Register Celery Beat nightly tasks."""
    # Run every night at 1:00 AM UTC
    sender.add_periodic_task(
        crontab(hour=1, minute=0),
        aggregate_daily_analytics.s(),
        name='aggregate_daily_analytics_cron'
    )

@celery_app.task(name="aggregate_daily_analytics")
def aggregate_daily_analytics():
    """
    Nightly cron job that scans chat_history and appointments
    for the previous 24 hours, aggregates them per business_id,
    and upserts into the analytics_daily warehouse.
    This guarantees dashboard queries remain under 50ms.
    """
    logger.info("Starting nightly Analytics Aggregation Cron Job...")
    
    if not supabase:
        logger.warning("Supabase not configured. Skipping analytics cron.")
        return "skipped"

    yesterday = datetime.utcnow() - timedelta(days=1)
    target_date_str = yesterday.strftime("%Y-%m-%d")

    try:
        # 1. Fetch all distinct businesses
        businesses_res = supabase.table('businesses').select('id').execute()
        businesses = businesses_res.data
        
        for b in businesses:
            business_id = b["id"]
            
            # 2. Count distinct messaging customers yesterday
            chat_res = supabase.table('chat_history') \
                .select('customer_phone') \
                .eq('role', 'user') \
                .gte('created_at', f"{target_date_str}T00:00:00Z") \
                .lte('created_at', f"{target_date_str}T23:59:59Z") \
                .execute()
                
            unique_phones = list(set(row["customer_phone"] for row in chat_res.data))
            unique_conversations = len(unique_phones)
            
            # 2.5 Categorize new vs repeat customers
            new_customers = 0
            repeat_customers = 0
            if unique_phones:
                customers_res = supabase.table('customers').select('*').in_('phone_number', unique_phones).execute()
                for cust in customers_res.data:
                    # Very simple ISO formatting check for same day account creation
                    if cust.get("created_at", "").startswith(target_date_str):
                        new_customers += 1
                    else:
                        repeat_customers += 1
            
            # 3. Count appointments booked FOR yesterday
            apt_res = supabase.table('appointments') \
                .select('id', count='exact') \
                .eq('business_id', business_id) \
                .gte('created_at', f"{target_date_str}T00:00:00Z") \
                .lte('created_at', f"{target_date_str}T23:59:59Z") \
                .execute()
                
            total_appointments = apt_res.count if apt_res.count else 0
            
            conversion_rate = 0.00
            if unique_conversations > 0:
                conversion_rate = round((total_appointments / unique_conversations) * 100, 2)
            
            # 4. Upsert into analytics_daily
            upsert_data = {
                "business_id": business_id,
                "metric_date": target_date_str,
                "total_conversations": unique_conversations,
                "appointments_booked": total_appointments,
                "new_customers": new_customers,
                "repeat_customers": repeat_customers,
                "conversion_rate": conversion_rate
            }
            
            supabase.table('analytics_daily').upsert(upsert_data, on_conflict="business_id, metric_date").execute()
            logger.info(f"Aggregated analytics for business {business_id} on {target_date_str}.")

        logger.info("Nightly Analytics Aggregation Complete.")
        return "success"
    
    except Exception as e:
        logger.error(f"Analytics Aggregation Cron Failed: {e}")
        raise
