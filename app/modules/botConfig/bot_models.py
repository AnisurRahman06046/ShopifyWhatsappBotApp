from sqlalchemy import Column, String, Integer
from app.core.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID


class BotConfig(Base):
    __tablename__ = "botConfig"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_clinetId = Column(String, nullable=True)
    bot_secretKey = Column(String, nullable=True)
    redirect_url = Column(String, nullable=True)
