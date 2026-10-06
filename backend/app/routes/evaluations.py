from fastapi import APIRouter, HTTPException
from app.services.storage import list_evaluations, get_evaluation
router=APIRouter()

@router.get("")
def evaluations():
    return list_evaluations()

@router.get("/{evaluation_id}")
def evaluation(evaluation_id:int):
    item=get_evaluation(evaluation_id)
    if not item: raise HTTPException(404,"Evaluation not found.")
    return item
