import hashlib
import math
import re

from fastapi import status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.models import KnowledgeDocument, UserMemory
from app.agent.schemas import KnowledgeDocumentCreate, KnowledgeDocumentRead, MemoryCreate, MemoryRead
from app.core.errors import AppError
from app.core.security import CurrentUser, Role


PLATFORM_DOCS = [
    ("Accounts and roles", "AgentTutor has student, tutor, and administrator accounts. Students browse tutors and request sessions. Tutors publish profiles and availability. Administrators manage platform operations."),
    ("Scheduling", "Tutors configure weekly availability and one-time blocked periods. Students request a time inside that availability. The tutor accepts or rejects the request. Either participant may cancel or propose a reschedule."),
    ("Session statuses", "A new session is requested. After the other participant accepts it, it is booked. Rejected and cancelled sessions appear in history. A reschedule becomes requested again until the other participant accepts."),
    ("Messaging and privacy", "Students and tutors communicate in private conversation threads. Administrators may inspect a conversation only when an active moderation report involves one of its participants."),
    ("Notifications", "AgentTutor creates in-app notifications for session requests, booking decisions, cancellations, reschedules, messages, and reminders."),
    ("AI safety", "The AgentTutor assistant may use read-only tools immediately. Actions that change data are stored as pending actions and execute only after the authenticated user confirms them."),
]


def embed_text(text: str, dimensions: int = 384) -> list[float]:
    """Small deterministic lexical embedding used when no model service is configured."""
    vector = [0.0] * dimensions
    for token in re.findall(r"[a-z0-9]+", text.casefold()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    length = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / length for value in vector]


class RAGService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ensure_platform_docs(self) -> None:
        existing = await self.db.scalar(
            select(KnowledgeDocument.id).where(KnowledgeDocument.category == "platform").limit(1)
        )
        if existing:
            return
        self.db.add_all([
            KnowledgeDocument(
                owner_user_id=None,
                category="platform",
                title=title,
                content=content,
                embedding=embed_text(f"{title} {content}"),
            )
            for title, content in PLATFORM_DOCS
        ])
        await self.db.commit()

    async def search(self, user: CurrentUser, query: str, category: str, limit: int = 4) -> list[KnowledgeDocumentRead]:
        if category == "platform":
            await self.ensure_platform_docs()
            ownership = KnowledgeDocument.owner_user_id.is_(None)
        elif category == "homework":
            ownership = KnowledgeDocument.owner_user_id == user.id
        else:
            raise AppError("Unsupported knowledge category")
        result = await self.db.execute(
            select(KnowledgeDocument)
            .where(KnowledgeDocument.category == category, ownership)
            .order_by(KnowledgeDocument.embedding.cosine_distance(embed_text(query)))
            .limit(limit)
        )
        return [KnowledgeDocumentRead.model_validate(item) for item in result.scalars().all()]

    async def add_document(self, user: CurrentUser, data: KnowledgeDocumentCreate) -> KnowledgeDocumentRead:
        if data.category == "platform" and user.role != Role.admin:
            raise AppError("Only administrators may add platform documentation", status.HTTP_403_FORBIDDEN)
        item = KnowledgeDocument(
            owner_user_id=None if data.category == "platform" else user.id,
            category=data.category,
            title=data.title,
            content=data.content,
            embedding=embed_text(f"{data.title} {data.content}"),
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return KnowledgeDocumentRead.model_validate(item)

    async def list_documents(self, user: CurrentUser, category: str) -> list[KnowledgeDocumentRead]:
        ownership = KnowledgeDocument.owner_user_id.is_(None) if category == "platform" else KnowledgeDocument.owner_user_id == user.id
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.category == category, ownership).order_by(KnowledgeDocument.created_at.desc())
        )
        return [KnowledgeDocumentRead.model_validate(item) for item in result.scalars().all()]

    async def delete_document(self, user: CurrentUser, document_id: str) -> None:
        item = await self.db.get(KnowledgeDocument, document_id)
        if item is None:
            raise AppError("Document not found", status.HTTP_404_NOT_FOUND)
        if item.owner_user_id != user.id and not (item.owner_user_id is None and user.role == Role.admin):
            raise AppError("You cannot delete this document", status.HTTP_403_FORBIDDEN)
        await self.db.delete(item)
        await self.db.commit()

    async def add_memory(self, user: CurrentUser, data: MemoryCreate) -> MemoryRead:
        item = UserMemory(
            user_id=user.id,
            kind=data.kind,
            content=data.content,
            sensitive=False,
            embedding=embed_text(data.content),
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return MemoryRead.model_validate(item)

    async def list_memories(self, user: CurrentUser) -> list[MemoryRead]:
        result = await self.db.execute(
            select(UserMemory).where(UserMemory.user_id == user.id).order_by(UserMemory.created_at.desc())
        )
        return [MemoryRead.model_validate(item) for item in result.scalars().all()]

    async def relevant_memories(self, user: CurrentUser, query: str, limit: int = 3) -> list[MemoryRead]:
        result = await self.db.execute(
            select(UserMemory)
            .where(UserMemory.user_id == user.id, UserMemory.sensitive.is_(False))
            .order_by(UserMemory.embedding.cosine_distance(embed_text(query)))
            .limit(limit)
        )
        return [MemoryRead.model_validate(item) for item in result.scalars().all()]

    async def delete_memory(self, user: CurrentUser, memory_id: str) -> None:
        result = await self.db.execute(
            delete(UserMemory).where(UserMemory.id == memory_id, UserMemory.user_id == user.id)
        )
        if result.rowcount == 0:
            raise AppError("Memory not found", status.HTTP_404_NOT_FOUND)
        await self.db.commit()
