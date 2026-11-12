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

router = APIRouter(prefix="/api/stream", tags=["stream"])

@router.post("")
def stream(data: StreamRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    conversation = get_chat_or_404(db, current_user.id, data.conversation_id)

    def events():
        text = ""
        count = 0
        stream = stream_chat([{"role": "user", "content": data.content}])
        for piece in stream:
            text += piece
            count += 1
            percent = min(99, round(count / settings.ollama_max_tokens * 100))
            yield f"data: {json.dumps({'token': piece, 'text': text, 'percent': percent})}\n\n"

        yield f"data: {json.dumps({'done': True, 'text': text, 'percent': 100})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")