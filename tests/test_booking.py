import pytest
from backend.services.booking_service import BookingService
from backend.services.availability_service import AvailabilityService
from unittest.mock import patch, MagicMock

def test_availability_service_closed_day():
    business_ctx = {
        "id": "b-123",
        "operating_hours": {
            "sunday": {"closed": True}
        }
    }
    slots = AvailabilityService.get_available_slots(business_ctx, "2026-03-15", "haircut") # 2026-03-15 is a Sunday
    assert slots == [] # Should be entirely empty for a closed day

@patch('backend.services.database_service.DatabaseService.create_appointment')
def test_booking_service_failure(mock_db_create):
    # Mock database throwing false due to double-booking constraint
    mock_db_create.return_value = False
    
    business_ctx = {
        "id": "b-123",
        "services_offered": {"haircut": {"duration": 45}}
    }
    
    # Should cleanly return False and not throw exceptions
    success = BookingService.create_appointment(
        business_ctx=business_ctx,
        customer_phone="12345",
        service_type="haircut",
        date_time_str="2026-03-15T10:00:00"
    )
    
    assert success is False
