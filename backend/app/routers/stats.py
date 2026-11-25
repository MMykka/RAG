# Stats router: GET /api/users/{user_id}/stats, a user's own usage numbers (403 for anyone else's)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user_id
from app.repositories.stats import get_user_stats
from app.schemas.stats import StatsOut


router = APIRouter(prefix="/api/users", tags=["stats"])


@router.get("/{user_id}/stats", response_model=StatsOut)
def get_stats(user_id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only view your own stats.")
    
    stats = get_user_stats(db, user_id)
    return StatsOut(**stats)