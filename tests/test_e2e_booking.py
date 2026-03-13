import pytest
from unittest.mock import patch, MagicMock
from backend.services.state_manager import StateManager
from backend.services.llm_service import LLMService

@patch.object(LLMService, 'classify_intent')
@patch('backend.services.state_manager.DatabaseService')
def test_full_agent_booking_workflow(mock_db, mock_classify):
    """Simulates a full end-to-end conversation using native LLM tool outputs."""
    
    # 1. User says "Hi I want a haircut"
    phone = "+19998887777"
    business_ctx = {"name": "Test Salon", "services_offered": [{"service_name": "haircut"}]}
    
    # DB mock: State INIT
    mock_db.get_conversation_state.return_value = {"current_state": "INIT", "booking_context": {}}
    mock_db.get_chat_history.return_value = []
    
    # LLM Mock: Extracts Intent but missing Date
    mock_classify.return_value = {"intent": "booking_request", "service": "haircut", "datetime": None}
    
    res = StateManager.process_message(phone, "Hi I want a haircut", business_ctx)
    
    # Expect transition to ASK_TIME
    assert "What time works for you" in res or "available times today" in res
    assert mock_db.update_conversation_state.called
    
    # 2. User says "Tomorrow at 4 PM"
    # DB Mock: State is now ASK_TIME and it saved the service into contexts
    mock_db.get_conversation_state.return_value = {
        "current_state": "ASK_TIME", 
        "booking_context": {"service": "haircut"}
    }
    
    # LLM Mock: Extracts exact datetime tool parameter
    mock_classify.return_value = {"intent": "booking_request", "service": "haircut", "datetime": "2026-03-14T16:00"}
    
    with patch('backend.services.state_manager.BookingService.create_appointment', return_value=True):
        res2 = StateManager.process_message(phone, "Tomorrow at 4 pm", business_ctx)
        
        # Expect successful booking
        assert "confirmed" in res2.lower()
        mock_db.update_conversation_state.assert_called_with(phone, "INIT", {})
