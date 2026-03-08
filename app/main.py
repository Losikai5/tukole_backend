from fastapi import FastAPI
from app.modules.User.routes import user_router 
from app.modules.Auth.routes import auth_router
from app.modules.Services.routes import service_router
from app.modules.Reviews.routes import review_router

version = "v2"
app = FastAPI(title="TUKOLE",description="A Mobile-First Service Marketplace for Uganda",version="1.0.0")
app.include_router(user_router, prefix=f"/api/{version}/users",tags=["User Management"])
app.include_router(auth_router, prefix=f"/api/{version}/auth",tags=["Authentication"])
app.include_router(service_router, prefix=f"/api/{version}/services",tags=["Services Management"])
app.include_router(review_router, prefix=f"/api/{version}/reviews",tags=["Reviews Management"])



@app.get("/")
def read_root():
    return {"Hello": "World"}