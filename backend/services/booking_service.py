from datetime import datetime, timedelta
from backend.services.database_service import DatabaseService
from backend.utils.logging import get_logger
from typing import Dict

logger = get_logger("booking_service")

class BookingService:
    @staticmethod
    def create_appointment(business_ctx: Dict, customer_phone: str, service_type: str, date_time_str: str) -> bool:
        """
        Booking Engine logic.
        Validates time and attempts database insertion.
        Relies on Postgres exclusion constraints `no_overlapping_appointments` to prevent double booking.
        """
        logger.info(f"Attempting to book: {customer_phone} for {service_type} at {date_time_str}")
        
        business_id = business_ctx.get("id")
        if not business_id:
            logger.error("Missing business context during booking.")
            return False

        try:
            # Try to parse the datetime_str given by LLM. 
            # Expecting ISO format "2026-03-15T16:00" as per LLM prompt requirements
            start_time = datetime.fromisoformat(date_time_str)
        except ValueError as e:
            logger.error(f"Invalid datetime format returned by LLM: {date_time_str}. Error: {e}")
            return False
            
        # Determine end time based on service duration
        services = business_ctx.get("services_offered", {})
        duration_minutes = services.get(service_type, {}).get("duration", 60)
        end_time = start_time + timedelta(minutes=duration_minutes)

        start_time_iso = start_time.isoformat()
        end_time_iso = end_time.isoformat()

        # Database creation function returns False if constraint is violated (double booked)
        success = DatabaseService.create_appointment(
            business_id=business_id,
            customer_phone=customer_phone,
            service_type=service_type,
            start_time=start_time_iso,
            end_time=end_time_iso
        )
        
        if success:
            logger.info("Booking successfully finalized.")
        else:
            logger.warning("Booking failed - possible double book detected.")
            
        return success
