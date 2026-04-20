from fastapi import APIRouter, Depends, HTTPException, status
from kombu.exceptions import OperationalError
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.dependencies import get_current_user, get_db
from app.models import ChatJob, ChatMessage, ChatSession, User
from app.schemas import (
    ChatJobStatusResponse,
    ChatCreateRequest,
    ChatMessageOut,
    ChatSessionOut,
    ChatUpdateRequest,
    SendMessageRequest,
    SendMessageResponse,
)

router = APIRouter(prefix="/api/chats", tags=["chats"])
FAILURE_ASSISTANT_MESSAGE = (
    "Система зараз перевантажена або з'єднання перервалося. "
    "Будь ласка, спробуйте ще раз трохи пізніше."
)


def _get_owned_chat_or_404(db: Session, user_id: int, chat_id: int) -> ChatSession:
    chat = db.query(ChatSession).filter(ChatSession.id == chat_id, ChatSession.user_id == user_id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


@router.get("", response_model=list[ChatSessionOut])
def list_chats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


@router.post("", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_chat(
    payload: ChatCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatSession:
    title = (payload.title or "").strip() or "New chat"
    chat = ChatSession(user_id=current_user.id, title=title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/{chat_id}", response_model=ChatSessionOut)
def get_chat(chat_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ChatSession:
    return _get_owned_chat_or_404(db, current_user.id, chat_id)


@router.patch("/{chat_id}", response_model=ChatSessionOut)
def rename_chat(
    chat_id: int,
    payload: ChatUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatSession:
    chat = _get_owned_chat_or_404(db, current_user.id, chat_id)
    chat.title = payload.title.strip()
    db.commit()
    db.refresh(chat)
    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    chat = _get_owned_chat_or_404(db, current_user.id, chat_id)
    db.delete(chat)
    db.commit()
    return None


@router.get("/{chat_id}/messages", response_model=list[ChatMessageOut])
def list_messages(
    chat_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ChatMessage]:
    chat = _get_owned_chat_or_404(db, current_user.id, chat_id)
    return db.query(ChatMessage).filter(ChatMessage.session_id == chat.id).order_by(ChatMessage.created_at.asc()).all()


@router.post("/{chat_id}/messages", response_model=SendMessageResponse)
def send_message(
    chat_id: int,
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SendMessageResponse:
    chat = _get_owned_chat_or_404(db, current_user.id, chat_id)
    message_text = payload.message.strip()
    if not message_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    user_message = ChatMessage(session_id=chat.id, role="user", content=message_text)
    db.add(user_message)
    db.flush()

    job = ChatJob(user_id=current_user.id, session_id=chat.id, user_message_id=user_message.id, status="queued")
    db.add(job)
    db.commit()
    db.refresh(user_message)
    db.refresh(job)
    try:
        celery_app.send_task("app.tasks.process_chat_job", args=[job.id])
    except OperationalError:
        fallback_message = ChatMessage(
            session_id=chat.id,
            role="assistant",
            content=FAILURE_ASSISTANT_MESSAGE,
        )
        db.add(fallback_message)
        db.flush()
        job.assistant_message_id = fallback_message.id
        job.status = "completed"
        job.error = "Queue is unavailable"
        db.commit()

    return SendMessageResponse(
        user_message=ChatMessageOut.model_validate(user_message),
        assistant_message=None,
        job_id=job.id,
        status=job.status,
    )


@router.get("/{chat_id}/jobs/{job_id}", response_model=ChatJobStatusResponse)
def get_job_status(
    chat_id: int,
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatJobStatusResponse:
    chat = _get_owned_chat_or_404(db, current_user.id, chat_id)
    job = (
        db.query(ChatJob)
        .filter(ChatJob.id == job_id, ChatJob.session_id == chat.id, ChatJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    user_message = db.query(ChatMessage).filter(ChatMessage.id == job.user_message_id).first()
    if not user_message:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Job message not found")

    assistant_message = None
    if job.assistant_message_id:
        assistant_message = db.query(ChatMessage).filter(ChatMessage.id == job.assistant_message_id).first()

    return ChatJobStatusResponse(
        job_id=job.id,
        chat_id=chat.id,
        status=job.status,
        user_message=ChatMessageOut.model_validate(user_message),
        assistant_message=ChatMessageOut.model_validate(assistant_message) if assistant_message else None,
        error=job.error,
    )
