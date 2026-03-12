from fastapi import FastAPI
from app.modules.User.routes import user_router 
from app.modules.Auth.routes import auth_router
from app.modules.Services.routes import service_router
from app.modules.Reviews.routes import review_router
from app.modules.Bookings.routes import booking_router
from app.modules.Payments.routes import payment_router
from app.modules.Providers.routes import provider_router
from app.modules.Disputes.routes import dispute_router
from app.modules.Notifications.routes import notification_router
from app.modules.Analytics.routes import analytics_router

version = "v2"
app = FastAPI(title="TUKOLE",description="A Mobile-First Service Marketplace for Uganda",version="1.0.0")
app.include_router(user_router, prefix=f"/api/{version}/users",tags=["User Management"])
app.include_router(auth_router, prefix=f"/api/{version}/auth",tags=["Authentication"])
app.include_router(service_router, prefix=f"/api/{version}/services",tags=["Services Management"])
app.include_router(review_router, prefix=f"/api/{version}/reviews",tags=["Reviews Management"])
app.include_router(booking_router, prefix=f"/api/{version}/bookings",tags=["Bookings Management"])
app.include_router(payment_router, prefix=f"/api/{version}/payments",tags=["Payments Management"])
app.include_router(provider_router, prefix=f"/api/{version}/providers",tags=["Providers Management"])
app.include_router(dispute_router, prefix=f"/api/{version}/disputes",tags=["Disputes Management"])
app.include_router(notification_router, prefix=f"/api/{version}/notifications",tags=["Notifications"])
app.include_router(analytics_router, prefix=f"/api/{version}/analytics",tags=["Analytics"])



@app.get("/")
def read_root():
    return {"Hello": "World"}