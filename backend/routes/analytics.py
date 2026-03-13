from fastapi import APIRouter, Depends
from backend.services.database_service import supabase
from backend.routes.api import get_current_business_id

router = APIRouter(prefix="/api", tags=["Analytics"])

@router.get("/analytics")
def get_analytics(business_id: str = Depends(get_current_business_id)):
    if not supabase: return []
    res = supabase.table("analytics_daily").select("*") \
        .eq("business_id", business_id) \
        .order("metric_date", desc=False) \
        .limit(30) \
        .execute()
    return res.data
