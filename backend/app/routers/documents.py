# Documents router: GET /api/documents, the files in the knowledge base (shared by every user).
# Documents are added with scripts/ingest_documents.py for now; there is no upload endpoint yet.
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.repositories.chunks import list_documents
from app.schemas.documents import DocumentOut

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def get_documents(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # login required; every logged-in user sees the same list (the knowledge base is shared)
    return list_documents(db)
