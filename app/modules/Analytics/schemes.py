from pydantic import BaseModel

class DashboardResponse(BaseModel):
    total_users: int
    total_bookings: int
    total_revenue: float
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_users": 150,
                "total_bookings": 45,
                "total_revenue": 12500.50
            }
        }
    }
