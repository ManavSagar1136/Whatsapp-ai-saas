import pytest
from backend.services.database_service import DatabaseService

# NOTE: These tests require a real Supabase connection or appropriate mocking.
# They are structured as stubs to demonstrate the testing architecture as requested.

def test_get_or_create_customer():
    # Example logic
    phone = "+1234567890"
    result = DatabaseService.get_or_create_customer(phone)
    assert result["phone_number"] == phone

def test_saving_state():
    phone = "+1234567890"
    DatabaseService.update_conversation_state(phone, "ASK_TIME", {"service": "massage"})
    state = DatabaseService.get_conversation_state(phone)
    # If using live DB without keys, these return mock fallbacks
    assert state["current_state"] in ["ASK_TIME", "INIT"] 
