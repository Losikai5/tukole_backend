from sqlalchemy.ext.asyncio import AsyncSession
class Auth_service:
    async def get_user_by_email(self,email:str,session:AsyncSession):
        pass
    async def user_exists(self,email:str,session:AsyncSession):
        pass
    async def create_user(self,user_data,session:AsyncSession):

        pass
    async def update_user(self,user_id:int,user_data,session:AsyncSession):
        pass