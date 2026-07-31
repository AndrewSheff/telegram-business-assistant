"""
Пакет моделей — импортируем все, чтобы Alembic их видел.
"""

from app.models.base import Base, BaseModel
from app.models.booking import Booking
from app.models.broadcast import Broadcast
from app.models.broadcast_log import BroadcastLog
from app.models.business_settings import BusinessSettings
from app.models.chat_message import ChatMessage
from app.models.client import Client
from app.models.faq import FaqItem
from app.models.knowledge_block import KnowledgeBlock
from app.models.schedule import WorkingHours
from app.models.schedule_exception import ScheduleException
from app.models.service import Service
from app.models.service_category import ServiceCategory
from app.models.user import User

__all__ = [
    "Base",
    "BaseModel",
    "Booking",
    "Broadcast",
    "BroadcastLog",
    "BusinessSettings",
    "ChatMessage",
    "Client",
    "FaqItem",
    "KnowledgeBlock",
    "WorkingHours",
    "ScheduleException",
    "Service",
    "ServiceCategory",
    "User",
]
