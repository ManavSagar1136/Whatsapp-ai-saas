import pytest
from backend.services.llm_service import LLMService

def test_intent_classification_greeting():
    result = LLMService.classify_intent("Hi there!")
    assert result.get("intent") in ["greeting", "faq", "unknown"]

def test_intent_classification_booking():
    result = LLMService.classify_intent("I want to book a haircut for tomorrow at 2 PM")
    assert result.get("intent") == "booking_request"
    assert result.get("service") in ["haircut", "Haircut", None] 
