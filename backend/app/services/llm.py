import json
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY, GEMINI_MODEL

def client():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured. Add it to backend/.env or the project root .env.")
    return genai.Client(api_key=GEMINI_API_KEY)

def generate_answer(question, context):
    prompt=f"""You are a grounded RAG assistant.
Answer the user's question using ONLY the supplied context.
If the context is insufficient, say that the information is not available in the provided documents.
Never invent facts. Keep the answer concise but complete.

QUESTION:
{question}

CONTEXT:
{context}
"""
    response=client().models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2)
    )
    return (response.text or "").strip()

def evaluate(question, answer, context):
    prompt=f"""You are an expert evaluator of Retrieval-Augmented Generation systems.
Evaluate the answer only against the supplied question and retrieved context.
Return ONLY valid JSON with this exact shape:
{{
  "answer_relevance": 0,
  "faithfulness": 0,
  "context_precision": 0,
  "completeness": 0,
  "overall_score": 0,
  "verdict": "Excellent|Good|Needs review|Poor",
  "reasoning": "short explanation",
  "issues": ["issue 1"]
}}
All numeric values must be integers from 0 to 100.

Definitions:
- answer_relevance: directly answers the user's question.
- faithfulness: claims are supported by retrieved context.
- context_precision: retrieved passages are relevant to the question.
- completeness: the answer covers the important information supported by the context.
- overall_score: balanced overall quality.

QUESTION:
{question}

GENERATED ANSWER:
{answer}

RETRIEVED CONTEXT:
{context}
"""
    response=client().models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json"
        )
    )
    raw=(response.text or "").strip()
    raw=raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()\n    data=json.loads(raw)
    fields=["answer_relevance","faithfulness","context_precision","completeness","overall_score"]
    for field in fields:
        data[field]=max(0,min(100,int(data.get(field,0))))
    data["verdict"]=str(data.get("verdict","Needs review"))
    data["reasoning"]=str(data.get("reasoning",""))
    data["issues"]=data.get("issues",[]) if isinstance(data.get("issues",[]),list) else []
    return data
