from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.models.schemas import Jurisdiction
from app.rag.classifier import classify_query

router = APIRouter()


class ClassifyIn(BaseModel):
    query: str
    jurisdiction: Jurisdiction | None = None


@router.post("/classify")
async def classify(inp: ClassifyIn) -> dict:
    res = classify_query(inp.query, jurisdiction_hint=inp.jurisdiction)
    return res.model_dump()
