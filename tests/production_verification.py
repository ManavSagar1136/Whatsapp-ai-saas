import httpx
import json
import time
from typing import Dict

# Configuration (Mock values for local testing)
BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{BASE_URL}/webhook"
HEALTH_URL = f"{BASE_URL}/health"
VERIFY_TOKEN = "whatsapp_local_webhook_secret_123"

def test_health_check():
    print("\n--- 🟢 Testing Health Check ---")
    try:
        response = httpx.get(HEALTH_URL)
        print(f"Status: {response.status_code}")
        print(f"Payload: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
        assert response.json()["status"] in ["operational", "degraded"]
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")

def test_webhook_verification():
    print("\n--- 🔵 Testing Webhook Verification (GET) ---")
    params = {
        "hub.mode": "subscribe",
        "hub.challenge": "123456789",
        "hub.verify_token": VERIFY_TOKEN
    }
    try:
        response = httpx.get(WEBHOOK_URL, params=params)
        print(f"Status: {response.status_code}")
        print(f"Challenge returned: {response.text}")
        assert response.status_code == 200
        assert response.text == "123456789"
    except Exception as e:
        print(f"❌ Webhook Verification Failed: {e}")

def test_mock_incoming_message():
    print("\n--- 🟠 Testing Mock Incoming Message (POST) ---")
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "123456", "phone_number_id": "TEST_PHONE_ID"},
                            "contacts": [{"profile": {"name": "Test User"}, "wa_id": "19998887777"}],
                            "messages": [
                                {
                                    "from": "19998887777",
                                    "id": f"msg_{int(time.time())}",
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": "Hi, I want to book a haircut tomorrow at 3pm"},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": "sha256=mock_signature" # Bypassed in code if APP_SECRET is mock
    }
    
    try:
        response = httpx.post(WEBHOOK_URL, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Payload: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        print("✅ Message successfully queued to Celery.")
    except Exception as e:
        print(f"❌ Incoming Message Test Failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Production Verification Suite...")
    test_health_check()
    test_webhook_verification()
    test_mock_incoming_message()
    print("\n🏁 Verification Complete.")
