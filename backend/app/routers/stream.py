# Stream router: POST /api/stream (SSE), comes in Week 2 Streaming Backend
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
from app.services.llm import stream_chat
from app.routers.conversations import get_chat_or_404
from app.schemas.stream import StreamRequest
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.config import settings
from app.repositories.conversations import save_message
from app.schemas.conversations import MessageCreate, SourceRef
from app.services.rag import retrieve_chunks, build_prompt


router = APIRouter(prefix="/api/stream", tags=["stream"])

@router.post("")
def stream(data: StreamRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    conversation = get_chat_or_404(db, current_user.id, data.conversation_id)
    user_msg = save_message(db, conversation, MessageCreate(role="user", content=data.content))

    def events():
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

    return StreamingResponse(events(), media_type="text/event-stream")