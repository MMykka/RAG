# Export router: GET /api/conversations/{id}/export?format=md|json
# Downloads one of the user's chats as a Markdown or JSON file.
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.routers.conversations import get_chat_or_404
from app.services import export

router = APIRouter(prefix="/api/conversations", tags=["export"])

MEDIA_TYPES = {"md": "text/markdown; charset=utf-8", "json": "application/json; charset=utf-8"}


@router.get("/{conversation_id}/export")
def export_chat(
    conversation_id: int,
    format: Literal["md", "json"] = Query("md"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    # Ownership first: another user's chat (or a missing one) is a 404, like everywhere else
    conversation = get_chat_or_404(db, user_id, conversation_id, with_messages=True)
    content = export.to_markdown(conversation) if format == "md" else export.to_json(conversation)

    # "attachment" tells the browser to download the file instead of showing it
    return Response(
        content=content,
        media_type=MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{export.filename(conversation, format)}"'},
    )
