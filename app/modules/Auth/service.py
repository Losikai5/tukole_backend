from sqlmodel.ext.asyncio import Asyncsession
class Auth_service:
    async def get_user_by_email(self,email:str,session:Asyncsession):
        pass