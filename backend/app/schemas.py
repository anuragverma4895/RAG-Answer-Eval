from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.config import SIMILARITY_THRESHOLD, TOP_K


class QueryRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=TOP_K, ge=1, le=10)
    similarity_threshold: float = Field(default=SIMILARITY_THRESHOLD, ge=0, le=1)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Question must contain at least two non-space characters.")
        return value


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
    issues: list[str] = Field(default_factory=list)


class QueryResponse(BaseModel):
    evaluation_id: int
    question: str
    answer: str
    model: str
    latency_ms: int
    retrieved_context: list[RetrievedChunk]
    evaluation: Evaluation
