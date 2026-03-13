from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from backend.services.database_service import supabase, redis_client
import json

router = APIRouter(prefix="/api", tags=["SaaS Dashboard"])

def get_current_business_id(authorization: str = Header(None)) -> str:
    """Decodes Supabase JWT to extract tenant constraints."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    
    if not supabase: return "mock-business-id"
    
    user_res = supabase.auth.get_user(token)
    if not user_res or not user_res.user:
        raise HTTPException(status_code=401, detail="Invalid Session")
    return user_res.user.id

# --- Appointments ---
@router.get("/appointments")
def get_appointments(business_id: str = Depends(get_current_business_id)):
    if not supabase: return []
    res = supabase.table("appointments").select("*").eq("business_id", business_id).order("start_time", desc=True).execute()
    return res.data

@router.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: str, business_id: str = Depends(get_current_business_id)):
    if not supabase: return {"status": "ok"}
    res = supabase.table("appointments").delete().eq("id", appointment_id).eq("business_id", business_id).execute()
    return {"status": "deleted"}

# --- Customers ---
@router.get("/customers")
def get_customers(business_id: str = Depends(get_current_business_id)):
    """Pull distinct customers interacting with this business."""
    if not supabase: return []
    # Simplified approximation: in reality joined via appointments
    res = supabase.table("appointments").select("customer_phone").eq("business_id", business_id).execute()
    unique_phones = list(set([row["customer_phone"] for row in res.data]))
    return [{"phone": p} for p in unique_phones]

# --- Settings ---
class OperatingHoursUpdate(BaseModel):
    operating_hours: Dict[str, Any]

@router.put("/settings/operating_hours")
def update_hours(payload: OperatingHoursUpdate, business_id: str = Depends(get_current_business_id)):
    if not supabase: return {"status": "ok"}
    # 1. Update DB
    supabase.table("businesses").update({"operating_hours": payload.operating_hours}).eq("id", business_id).execute()
    
    # 2. Invalidate Cache
    bus_res = supabase.table("businesses").select("whatsapp_number_id").eq("id", business_id).execute()
    if bus_res.data:
        redis_client.delete(f"business_ctx:{bus_res.data[0]['whatsapp_number_id']}")
        
    return {"status": "updated"}

class FaqUpdate(BaseModel):
    faq_context: str

@router.put("/settings/faq")
def update_faq(payload: FaqUpdate, business_id: str = Depends(get_current_business_id)):
    if not supabase: return {"status": "ok"}
    supabase.table("businesses").update({"faq_context": payload.faq_context}).eq("id", business_id).execute()
    
    bus_res = supabase.table("businesses").select("whatsapp_number_id").eq("id", business_id).execute()
    if bus_res.data:
        redis_client.delete(f"business_ctx:{bus_res.data[0]['whatsapp_number_id']}")
        
    return {"status": "updated"}

class ServiceItem(BaseModel):
    service_name: str
    duration_minutes: int
    price: float

class ServicesUpdate(BaseModel):
    services: List[ServiceItem]

@router.put("/settings/services")
def update_services(payload: ServicesUpdate, business_id: str = Depends(get_current_business_id)):
    """Iteration 3: Updates relational business_services table natively."""
    if not supabase: return {"status": "ok"}
    
    # Fully replace services for simplicity
    supabase.table("business_services").delete().eq("business_id", business_id).execute()
    
    inserts = []
    for s in payload.services:
        inserts.append({
            "business_id": business_id,
            "service_name": s.service_name,
            "duration_minutes": s.duration_minutes,
            "price": s.price
        })
        
    if inserts:
        supabase.table("business_services").insert(inserts).execute()
        
    bus_res = supabase.table("businesses").select("whatsapp_number_id").eq("id", business_id).execute()
    if bus_res.data:
        redis_client.delete(f"business_ctx:{bus_res.data[0]['whatsapp_number_id']}")
        
    return {"status": "updated"}
