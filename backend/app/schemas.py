from typing import Any, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)
    similarity_threshold: float = Field(default=0.25, ge=0, le=1)

class RetrievedChunk(BaseModel):
    id: str
    document_name: str
    document_id: str
    chunk_index: int
    page_number: Optional[int] = None
    similarity: float
    text: str

class Evaluation(BaseModel):
    answer_relevance: int
    faithfulness: int
    context_precision: int
    completeness: int
    overall_score: int
    verdict: str
    reasoning: str
    issues: list[str] = []

class QueryResponse(BaseModel):
    evaluation_id: int
    question: str
    answer: str
    model: str
    latency_ms: int
    retrieved_context: list[RetrievedChunk]
    evaluation: Evaluation
