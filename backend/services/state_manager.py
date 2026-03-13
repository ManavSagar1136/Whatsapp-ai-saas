from backend.services.database_service import DatabaseService
from backend.services.llm_service import LLMService
from backend.services.booking_service import BookingService
from backend.services.availability_service import AvailabilityService
from backend.utils.logging import get_logger
from datetime import datetime

logger = get_logger("state_manager")

class StateManager:
    """Manages the conversation state machine for bookings."""
    
    @staticmethod
    def process_message(phone_number: str, user_message: str, business_ctx: dict) -> str:
        logger.info(f"Processing message from {phone_number}")
        
        state_data = DatabaseService.get_conversation_state(phone_number)
        current_state = state_data.get("current_state", "INIT")
        booking_ctx = state_data.get("booking_context", {})
        
        chat_history = DatabaseService.get_chat_history(phone_number)
        intent_data = LLMService.classify_intent(user_message, chat_history, business_ctx)
        intent = intent_data.get("intent", "unknown")
        
        logger.debug(f"Current State: {current_state} | Intent: {intent}")

        # Cancel Flow
        if intent == "cancel_booking":
            DatabaseService.update_conversation_state(phone_number, "INIT", {})
            return "Your booking process has been cancelled. Let me know if you need anything else!"

        # Conversational / FAQ Flow
        if intent in ["greeting", "faq", "unknown"] and current_state == "INIT":
            chat_history = DatabaseService.get_chat_history(phone_number)
            return LLMService.generate_response(business_ctx, chat_history, user_message)

        # State Machine Transitions
        if intent == "booking_request" or current_state != "INIT":
            
            if current_state == "INIT":
                current_state = "ASK_SERVICE"
                
            # Extract slots from intent
            if intent_data.get("service"):
                booking_ctx["service"] = intent_data.get("service")
            if intent_data.get("datetime"):
                booking_ctx["datetime"] = intent_data.get("datetime") # Should be ISO

            # State Logic
            if current_state == "ASK_SERVICE":
                if "service" not in booking_ctx:
                    DatabaseService.update_conversation_state(phone_number, "ASK_SERVICE", booking_ctx)
                    service_names = [s.get("service_name") for s in business_ctx.get('services_offered', []) if isinstance(s, dict)]
                    return f"I can help you book! What service would you like? We offer: {service_names}"
                else:
                    current_state = "ASK_TIME"
                    
            if current_state == "ASK_TIME":
                if "datetime" not in booking_ctx:
                    DatabaseService.update_conversation_state(phone_number, "ASK_TIME", booking_ctx)
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    slots = AvailabilityService.get_available_slots(business_ctx, today_str, booking_ctx["service"])
                    return f"Great, a {booking_ctx['service']}. Some available times today are {slots}. What time works for you? (You can say 'tomorrow' too)"
                else:
                    current_state = "CONFIRM_BOOKING"
                    
            if current_state == "CONFIRM_BOOKING":
                # Finalize booking
                success = BookingService.create_appointment(
                    business_ctx=business_ctx,
                    customer_phone=phone_number,
                    service_type=booking_ctx["service"],
                    date_time_str=booking_ctx["datetime"]
                )
                
                if success:
                    DatabaseService.update_conversation_state(phone_number, "BOOKED", {})
                    # reset back to INIT quietly to allow future messages
                    DatabaseService.update_conversation_state(phone_number, "INIT", {})
                    return f"Done! Your {booking_ctx['service']} is confirmed for {booking_ctx['datetime']}. See you then!"
                else:
                    # Clear date to force them to pick again
                    booking_ctx.pop("datetime", None)
                    DatabaseService.update_conversation_state(phone_number, "ASK_TIME", booking_ctx)
                    return "Sorry, I couldn't secure that specific time. Someone else might have booked it, or it's misformatted. Can we try another time?"
            
        return "I'm not exactly sure what you mean. Do you want to book an appointment or ask about our services?"
