import logging

from sqlalchemy import text

from app.config import settings
from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import ChatJob, ChatMessage, ChatSession
from app.ollama_client import generate_assistant_reply, generate_embedding

logger = logging.getLogger(__name__)
FAILURE_ASSISTANT_MESSAGE = (
    "Система зараз перевантажена або з'єднання перервалося. "
    "Будь ласка, спробуйте ще раз трохи пізніше."
)


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"


def _build_context_messages(db, session_id: int, user_message_id: int) -> list[dict[str, str]]:
    recent_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(settings.retrieval_recent_count)
        .all()
    )
    recent_messages = list(reversed(recent_messages))
    recent_ids = {msg.id for msg in recent_messages}

    current_user_message = db.query(ChatMessage).filter(ChatMessage.id == user_message_id).first()
    if not current_user_message:
        return [{"role": msg.role, "content": msg.content} for msg in recent_messages]

    query_embedding = None
    try:
        query_embedding = generate_embedding(current_user_message.content)
        if len(query_embedding) >= settings.embedding_dimensions:
            query_embedding = query_embedding[: settings.embedding_dimensions]
            current_user_message.embedding = query_embedding
            db.commit()
    except Exception:
        query_embedding = None

    semantic_ids: set[int] = set()
    if query_embedding is not None:
        vector_param = _vector_literal(query_embedding)
        rows = db.execute(
            text(
                """
                SELECT id
                FROM chat_messages
                WHERE session_id = :session_id
                  AND id <> :user_message_id
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:query_embedding AS vector)
                LIMIT :top_k
                """
            ),
            {
                "session_id": session_id,
                "user_message_id": user_message_id,
                "query_embedding": vector_param,
                "top_k": settings.retrieval_top_k,
            },
        ).fetchall()
        semantic_ids = {row[0] for row in rows}

    selected_ids = recent_ids | semantic_ids | {user_message_id}
    context_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.id.in_(selected_ids))
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [{"role": msg.role, "content": msg.content} for msg in context_messages]


@celery_app.task(name="app.tasks.process_chat_job")
def process_chat_job(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.query(ChatJob).filter(ChatJob.id == job_id).first()
        if not job:
            logger.warning("Chat job %s not found", job_id)
            return
        if job.status == "completed":
            return

        job.status = "processing"
        job.error = None
        db.commit()

        ollama_messages = _build_context_messages(db, job.session_id, job.user_message_id)
        assistant_text = generate_assistant_reply(ollama_messages)

        assistant_message = ChatMessage(session_id=job.session_id, role="assistant", content=assistant_text)
        db.add(assistant_message)
        db.flush()
        try:
            assistant_embedding = generate_embedding(assistant_text)
            if len(assistant_embedding) >= settings.embedding_dimensions:
                assistant_message.embedding = assistant_embedding[: settings.embedding_dimensions]
        except Exception:
            logger.warning("Assistant embedding failed for message %s", assistant_message.id)

        chat = db.query(ChatSession).filter(ChatSession.id == job.session_id).first()
        if chat and chat.title == "New chat":
            user_message = db.query(ChatMessage).filter(ChatMessage.id == job.user_message_id).first()
            if user_message:
                chat.title = user_message.content[:80]

        job.assistant_message_id = assistant_message.id
        job.status = "completed"
        job.error = None
        db.commit()
    except Exception as exc:
        logger.exception("Failed processing chat job %s: %s", job_id, exc)
        job = db.query(ChatJob).filter(ChatJob.id == job_id).first()
        if job:
            fallback_message = ChatMessage(
                session_id=job.session_id,
                role="assistant",
                content=FAILURE_ASSISTANT_MESSAGE,
            )
            db.add(fallback_message)
            db.flush()
            job.assistant_message_id = fallback_message.id
            job.status = "completed"
            job.error = str(exc)[:2000]
            db.commit()
    finally:
        db.close()
