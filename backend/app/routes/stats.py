from fastapi import APIRouter
from app.services.storage import stats
router=APIRouter()
@router.get("/stats")
def get_stats():
    return stats()
