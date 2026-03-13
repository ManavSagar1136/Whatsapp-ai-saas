import pytest
from unittest.mock import patch, MagicMock
from backend.routes.webhook import verify_meta_signature, check_rate_limit
from fastapi import HTTPException
import json
import hashlib
import hmac
from backend.config import settings

def test_verify_signature_valid():
    """Verify that a valid X-Hub-Signature-256 passes correctly."""
    # Settings fallback
    secret = settings.whatsapp_app_secret
    payload = b'{"object": "whatsapp_business_account"}'
    
    expected_hash = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    signature_header = f"sha256={expected_hash}"
    
    # Should not raise exception
    verify_meta_signature(payload, signature_header)

def test_verify_signature_invalid():
    """Verify that a mangled signature correctly throws a 403."""
    payload = b'{"object": "whatsapp_business_account"}'
    signature_header = "sha256=invalidhash123"
    
    with pytest.raises(HTTPException) as excinfo:
        verify_meta_signature(payload, signature_header)
    
    assert excinfo.value.status_code == 403

@patch('backend.routes.webhook.redis_client')
def test_rate_limiting_ok(mock_redis):
    # Mocking < 20 messages in the sorted set
    mock_redis.zcard.return_value = 5 
    # Should not throw HTTPException
    check_rate_limit("1234567890")
    assert mock_redis.zadd.called

@patch('backend.routes.webhook.redis_client')
def test_rate_limiting_exceeded(mock_redis):
    # Mocking > 20 messages in the last 60 seconds
    mock_redis.zcard.return_value = 21 
    
    with pytest.raises(HTTPException) as excinfo:
        check_rate_limit("1234567890")
    
    assert excinfo.value.status_code == 429
    assert excinfo.value.detail == "Too Many Requests"

@patch('backend.worker.DatabaseService.is_message_processed')
def test_worker_idempotency(mock_is_processed):
    """Ensure the worker aborts early if the idempotency DB check is triggered."""
    from backend.worker import process_message_task
    
    # Mock DB saying message already hit the webhook and was completed
    mock_is_processed.return_value = True 
    
    msg = {"id": "wamid.123", "from": "+11234567"}
    
    # Needs to bypass bind=True behavior manually or test the function directly
    # Call the original wrapped function to bypass Celery context in simple test
    result = process_message_task.__wrapped__(None, "phone_id_1", msg)
    
    assert result == "skipped_duplicate"
