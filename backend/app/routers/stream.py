# Stream router: POST /api/stream (SSE): retrieves document chunks, streams Llama's answer, saves both messages
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
import json
from app.services.llm import stream_chat
from app.routers.conversations import get_chat_or_404
from app.schemas.stream import StreamRequest
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user_id, limiter
from app.config import settings
from app.repositories.conversations import save_message
from app.schemas.conversations import MessageCreate, SourceRef
from app.services.rag import retrieve_chunks, build_prompt
from app.services.cache import take_slot, release_slot


router = APIRouter(prefix="/api/stream", tags=["stream"])

@router.post("")
# at most 20 questions per minute per user (counted by user_or_ip in dependencies.py); the 21st gets 429
@limiter.limit("20/minute")
def stream(request: Request, data: StreamRequest, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    
    conversation = get_chat_or_404(db, user_id, data.conversation_id)
    # Only MAX_GENERATIONS answers may be written at the same time (shared Redis counter, services/cache.py).
    # No free slot: refuse before anything is saved or Llama is called.
    if not take_slot():
        raise HTTPException(status_code=503, detail="The server is busy. Please try again.")

    try:
        user_msg = save_message(db, conversation, MessageCreate(role="user", content=data.content))
    except Exception:
        release_slot()  # the answer will never start, so give the slot back now
        raise

    released = False

    def release_once():
        # two paths below can both try to give the slot back; only the first one counts
        nonlocal released
        if not released:
            released = True
            release_slot()

    def events():
        # finally: the slot is given back when the answer ends or fails
        try:
            yield from answer_events()
        finally:
            release_once()

    def after_response():
        # Starlette runs this after every response, also when the user presses Stop or closes the page.
        # In that case it stops reading but never closes the generator, so its finally above would not run
        # (and the Ollama call would stay open): close it here, which runs that finally.
        try:
            body.close()
        except ValueError:
            pass  # still running in its thread right now; its own finally releases the slot when it stops
        release_once()

    def answer_events():
        text = ""
        count = 0
        usage = {}

        try:
            chunks = retrieve_chunks(db, data.content)
            messages = build_prompt(data.content, chunks)
            sources = [SourceRef(source=c.source, chunk_index=c.chunk_index) for c in chunks]
            stream = stream_chat(messages, usage)

            for piece in stream:

                text += piece
                count += 1
                percent = min(99, round(count / settings.ollama_max_tokens * 100))

                yield f"data: {json.dumps({'token': piece, 'text': text, 'percent': percent})}\n\n"
        except Exception as e:
            print("Stream Failed", e)
            yield f"data: {json.dumps({'error': 'The AI stopped answering. Please try again.', 'text': text})}\n\n"
            return 


        if text:
            user_msg.tokens_used = usage.get("prompt")
            save_message(db, conversation, MessageCreate(role="assistant", content=text, tokens_used=usage.get("answer"), sources=sources or None))

        
        yield f"data: {json.dumps({'done': True, 'text': text, 'percent': 100, 'sources': [s.model_dump() for s in sources]})}\n\n"

    body = events()
    return StreamingResponse(body, media_type="text/event-stream", background=BackgroundTask(after_response))