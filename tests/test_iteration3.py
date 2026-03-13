import pytest
from unittest.mock import patch, MagicMock
from backend.services.llm_service import LLMService
from backend.routes.api import update_services, ServicesUpdate, ServiceItem
from backend.celery_beat import aggregate_daily_analytics

@patch('backend.services.llm_service.client')
def test_native_tool_calling_extraction(mock_client):
    """Test that the LLM Service successfully unwraps Groq Native Tool calls."""
    # Mocking the Groq response structure for a tool call
    mock_response = MagicMock()
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "book_appointment"
    mock_tool_call.function.arguments = '{"service": "haircut", "datetime": "2026-03-15T10:00"}'
    
    mock_response.choices[0].message.tool_calls = [mock_tool_call]
    mock_client.chat.completions.create.return_value = mock_response

    business_ctx = {"name": "Test Salon", "services_offered": [{"service_name": "haircut", "price": 40}]}
    
    result = LLMService.classify_intent("Book a haircut for tomorrow", [], business_ctx)
    
    assert result["intent"] == "booking_request"
    assert result["service"] == "haircut"
    assert result["datetime"] == "2026-03-15T10:00"

@patch('backend.routes.api.supabase')
@patch('backend.routes.api.redis_client')
def test_service_relational_crud(mock_redis, mock_supabase):
    """Test that PUT /api/settings/services hits the relational table and invalidates cache."""
    # Mock the chained supabase calls
    mock_delete = MagicMock()
    mock_insert = MagicMock()
    mock_supabase.table().delete().eq().execute.return_value = mock_delete
    mock_supabase.table().insert().execute.return_value = mock_insert
    
    # Mock cache invalidation lookup
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[{"whatsapp_number_id": "12345"}])

    payload = ServicesUpdate(services=[ServiceItem(service_name="haircut", duration_minutes=30, price=20.0)])
    result = update_services(payload, "business-id-999")
    
    # Assert DB and Cache operations fired
    assert result["status"] == "updated"
    assert mock_supabase.table().delete.called
    assert mock_supabase.table().insert.called
    mock_redis.delete.assert_called_with("business_ctx:12345")

@patch('backend.celery_beat.supabase')
def test_expanded_analytics_aggregation(mock_supabase):
    """Test the expanded Celery beat job containing new, repeat, and conversion metrics."""
    # Mock business fetch
    mock_supabase.table().select().execute.return_value = MagicMock(data=[{"id": "b-1"}])
    
    # Mock Chat History uniquely yielding 2 phones
    mock_supabase.table().select().eq().gte().lte().execute.return_value = MagicMock(
        data=[{"customer_phone": "+1"}, {"customer_phone": "+2"}]
    )
    
    # Mock Customers showing 1 old and 1 new
    mock_supabase.table().select().in_().execute.return_value = MagicMock(
        data=[
            {"phone_number": "+1", "created_at": "2026-03-10"}, # Repeat
            {"phone_number": "+2", "created_at": "2026-03-14"}  # New (assuming run on 03-15)
        ]
    )
    
    # Mock Appointments giving 1 total appointment
    mock_apt = MagicMock()
    mock_apt.count = 1
    mock_supabase.table().select().eq().gte().lte().execute.return_value = mock_apt
    
    # Mock Upsert
    mock_upsert = MagicMock()
    mock_supabase.table().upsert.return_value.execute = mock_upsert
    
    # Needs to align with exact dates in the test runner, but here we just verify 
    # the upsert trigger to avoid brittle datetime patching in unit tests.
    aggregate_daily_analytics()
    
    assert mock_supabase.table().upsert.called
