from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from .bot_repository import BotAppRepository
from pydantic import BaseModel

router = APIRouter()


class BotAppCreateSchema(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str


@router.get("/botapp/register")
async def serve_register_form():
    # Serve your static HTML page for the form here
    return FileResponse("static/botapp_register.html")


@router.post("/botapp/register")
async def botapp_register(
    data: BotAppCreateSchema, db: AsyncSession = Depends(get_async_db)
):
    repo = BotAppRepository(db)
    existing = await repo.get_app()
    if existing:
        await db.delete(existing)
        await db.commit()
    await repo.create_app(
        bot_clinetId=data.client_id,
        bot_secretKey=data.client_secret,
        redirect_url=data.redirect_uri,
    )
    return {"message": "Bot app credentials saved successfully."}
