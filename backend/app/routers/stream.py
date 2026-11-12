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

router = APIRouter(prefix="/api/stream", tags=["stream"])

@router.post("")
def stream(data: StreamRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    conversation = get_chat_or_404(db, current_user.id, data.conversation_id)

    def events():
        stream = stream_chat([{"role": "user", "content": data.content}])
        for piece in stream:
            yield f"data: {json.dumps({'token': piece})}\n\n"

        yield f"data: {json.dumps({'done': True})}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")