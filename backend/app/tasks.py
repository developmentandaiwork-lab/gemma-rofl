import logging

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import ChatJob, ChatMessage, ChatSession
from app.ollama_client import generate_assistant_reply

logger = logging.getLogger(__name__)
FAILURE_ASSISTANT_MESSAGE = (
    "Система зараз перевантажена або з'єднання перервалося. "
    "Будь ласка, спробуйте ще раз трохи пізніше."
)


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

        history = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == job.session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in history]
        assistant_text = generate_assistant_reply(ollama_messages)

        assistant_message = ChatMessage(session_id=job.session_id, role="assistant", content=assistant_text)
        db.add(assistant_message)
        db.flush()

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
