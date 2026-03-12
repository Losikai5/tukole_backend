from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import RoleChecker
from .services import AnalyticsService
from .schemes import DashboardResponse

analytics_router = APIRouter()
analytics_service = AnalyticsService()

@analytics_router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    session: AsyncSession = Depends(get_db),
    _: bool = Depends(RoleChecker(["admin"]))
):

    users = await analytics_service.total_users(session)
    bookings = await analytics_service.total_bookings(session)
    revenue = await analytics_service.total_revenue(session)

    return {
        "total_users": users,
        "total_bookings": bookings,
        "total_revenue": revenue
    }