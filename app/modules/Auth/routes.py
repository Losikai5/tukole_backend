from fastapi import APIRouter, Depends

auth_router = APIRouter()

@auth_router.get("/login")
async def login():
    pass
@auth_router.post("/register")
async def register():
    pass
@auth_router.post("/logout")
async def logout():
    pass
@auth_router.post("/refresh-token")
async def refresh_token():
    pass
@auth_router.get("/me")
async def get_current_user():
    pass
