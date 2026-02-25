from fastapi import FastAPI
from app.modules.User.routes import user_router 
from app.modules.Auth.routes import auth_router

version = "v2"
app = FastAPI(title="TUKOLE",description="A simple booking system",version="1.0.0")
app.include_router(user_router, prefix=f"/api/{version}/users",tags=["User Management"])
app.include_router(auth_router, prefix=f"/api/{version}/auth",tags=["Authentication"])


@app.get("/")
def read_root():
    return {"Hello": "World"}