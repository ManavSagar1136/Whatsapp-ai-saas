from datetime import datetime, timedelta
from typing import List, Dict
from backend.services.database_service import DatabaseService
from backend.utils.logging import get_logger

logger = get_logger("availability_service")

class AvailabilityService:
    @staticmethod
    def get_available_slots(business_ctx: Dict, date_str: str, service_type: str = None) -> List[str]:
        """
        Calculates available appointment slots for a given date.
        1. Reads operating_hours.
        2. Reads services_offered to determine block size.
        3. Reads existing appointments from DB.
        4. Generates list of free slots.
        """
        logger.info(f"Checking availability for {date_str} for service: {service_type}")
        business_id = business_ctx.get("id")
        
        # 1 & 2. Fallbacks for missing context
        # Assumes default block size is 60 mins if service not found or unspecified
        duration_minutes = 60
        if service_type:
            services = business_ctx.get("services_offered", {})
            duration_minutes = services.get(service_type, {}).get("duration", 60)
            
        # Parse date and get day of week
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning("Invalid date format requested for availability.")
            return []
            
        day_of_week = target_date.strftime("%A").lower()
        operating_hours = business_ctx.get("operating_hours", {})
        
        day_hours = operating_hours.get(day_of_week)
        if not day_hours or day_hours.get("closed", False):
            return [] # Closed on this day
            
        open_time_str = day_hours.get("open", "09:00")
        close_time_str = day_hours.get("close", "17:00")
        
        # 3. Read existing appointments
        existing_appointments = DatabaseService.get_appointments_by_date(business_id, date_str)
        booked_times = []
        for appt in existing_appointments:
            # Simplistic overlap check based strictly on start times parsed as ISO
            start_iso = appt.get("start_time")
            if start_iso:
                dt = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
                booked_times.append(dt.strftime("%H:%M"))

        # 4. Generate free slots
        available_slots = []
        
        open_time = datetime.strptime(f"{date_str} {open_time_str}", "%Y-%m-%d %H:%M")
        close_time = datetime.strptime(f"{date_str} {close_time_str}", "%Y-%m-%d %H:%M")
        
        current_time = open_time
        
        # Increment by 30 mins, but require a contiguous block of duration_minutes
        step = timedelta(minutes=30)
        req_duration = timedelta(minutes=duration_minutes)
        
        while current_time + req_duration <= close_time:
            time_str = current_time.strftime("%H:%M")
            # If this starting time isn't strictly booked (simplistic check for MVP)
            if time_str not in booked_times:
                available_slots.append(current_time.strftime("%I:%M %p"))
                
            current_time += step
            
        logger.debug(f"Generated slots: {available_slots}")
        # Return a subset so we don't overwhelm the WhatsApp message
        return available_slots[:5]
