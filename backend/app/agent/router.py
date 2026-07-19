from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.rag import RAGService
from app.agent.schemas import (
    ActionDecisionResponse,
    AgentConversationRead,
    AgentMessageRequest,
    AgentMessageResponse,
    KnowledgeDocumentCreate,
    KnowledgeDocumentRead,
    MemoryCreate,
    MemoryRead,
)
from app.agent.service import AgentService
from app.core.database import get_db_session
from app.core.security import CurrentUser, get_current_user


router = APIRouter()


@router.post("/chat", response_model=AgentMessageResponse)
async def chat(request: AgentMessageRequest, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await AgentService(db).respond(current_user, request)


@router.get("/conversations", response_model=list[AgentConversationRead])
async def conversations(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await AgentService(db).list_conversations(current_user)


@router.post("/actions/{action_id}/confirm", response_model=ActionDecisionResponse)
async def confirm_action(action_id: str, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await AgentService(db).confirm_action(current_user, action_id)


@router.post("/actions/{action_id}/reject", response_model=ActionDecisionResponse)
async def reject_action(action_id: str, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await AgentService(db).reject_action(current_user, action_id)


@router.get("/documents", response_model=list[KnowledgeDocumentRead])
async def documents(category: str = "homework", current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await RAGService(db).list_documents(current_user, category)


@router.post("/documents", response_model=KnowledgeDocumentRead, status_code=status.HTTP_201_CREATED)
async def add_document(data: KnowledgeDocumentCreate, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await RAGService(db).add_document(current_user, data)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await RAGService(db).delete_document(current_user, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/memories", response_model=list[MemoryRead])
async def memories(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await RAGService(db).list_memories(current_user)


@router.post("/memories", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
async def add_memory(data: MemoryCreate, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await RAGService(db).add_memory(current_user, data)


@router.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: str, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await RAGService(db).delete_memory(current_user, memory_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
