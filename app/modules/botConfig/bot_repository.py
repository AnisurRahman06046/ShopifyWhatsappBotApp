# app/modules/BotApp/bot_app_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from .bot_models import BotConfig
from sqlalchemy import select


class BotAppRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_app(
        self, bot_clinetId: str, bot_secretKey: str, redirect_url: str
    ):
        app = BotConfig(
            bot_clinetId=bot_clinetId,
            bot_secretKey=bot_secretKey,
            redirect_url=redirect_url,
        )
        self.db.add(app)
        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def get_app(self):
        result = await self.db.execute(select(BotConfig).limit(1))
        return result.scalar_one_or_none()
