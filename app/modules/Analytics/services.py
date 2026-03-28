from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import User, Booking, Payment

class AnalyticsService:

    async def total_users(self, session: AsyncSession):

        statement = select(func.count(User.uid))

        result = await session.exec(statement)

        return result.one()


    async def total_bookings(self, session: AsyncSession):

        statement = select(func.count(Booking.uid)).where(Booking.deleted_at == None)

        result = await session.exec(statement)

        return result.one()


    async def total_revenue(self, session: AsyncSession):

        statement = select(func.sum(Payment.amount)).where(
            Payment.status == "released"
        )

        result = await session.exec(statement)

        return result.one() or 0.0
