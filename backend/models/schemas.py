from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Contact(BaseModel):
    wa_id: str
    profile: Dict[str, str]

class MessageData(BaseModel):
    from_: str = Field(alias="from")
    id: str
    timestamp: str
    text: Optional[Dict[str, str]] = None
    type: str

class WebhookMetadata(BaseModel):
    display_phone_number: str
    phone_number_id: str

class WebhookValue(BaseModel):
    messaging_product: str
    metadata: WebhookMetadata
    contacts: Optional[List[Contact]] = None
    messages: Optional[List[MessageData]] = None

class WebhookChange(BaseModel):
    field: str
    value: WebhookValue

class WebhookEntry(BaseModel):
    id: str
    changes: List[WebhookChange]

class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: List[WebhookEntry]

class IntentClassification(BaseModel):
    intent: str
    service: Optional[str] = None
    datetime_str: Optional[str] = None

class AppointmentSchema(BaseModel):
    business_id: str
    customer_phone: str
    service_type: str
    start_time: str
    end_time: str
    status: str = "CONFIRMED"
