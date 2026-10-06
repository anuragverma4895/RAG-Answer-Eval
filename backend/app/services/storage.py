import json
import sqlite3
from datetime import datetime, timezone
from app.config import SQLITE_PATH

def connection():
    return sqlite3.connect(SQLITE_PATH)

def init_db():
    with connection() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            chunks INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            retrieved_documents TEXT NOT NULL,
            answer_relevance INTEGER NOT NULL,
            faithfulness INTEGER NOT NULL,
            context_precision INTEGER NOT NULL,
            completeness INTEGER NOT NULL,
            overall_score INTEGER NOT NULL,
            verdict TEXT NOT NULL,
            reasoning TEXT NOT NULL,
            issues TEXT NOT NULL,
            latency_ms INTEGER NOT NULL,
            model TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")

def create_document(doc_id, name, file_type, size_bytes):
    now=datetime.now(timezone.utc).isoformat()
    with connection() as db:
        db.execute("INSERT INTO documents(id,name,file_type,size_bytes,status,created_at) VALUES(?,?,?,?,?,?)",
                   (doc_id,name,file_type,size_bytes,"processing",now))

def update_document(doc_id, chunks, status):
    with connection() as db:
        db.execute("UPDATE documents SET chunks=?, status=? WHERE id=?", (chunks,status,doc_id))

def list_documents():
    with connection() as db:
        rows=db.execute("SELECT id,name,file_type,size_bytes,chunks,status,created_at FROM documents ORDER BY created_at DESC").fetchall()
    keys=["id","name","file_type","size_bytes","chunks","status","created_at"]
    return [dict(zip(keys,r)) for r in rows]

def delete_document(doc_id):
    with connection() as db:
        db.execute("DELETE FROM documents WHERE id=?", (doc_id,))

def create_evaluation(question, answer, retrieved_documents, evaluation, latency_ms, model):
    now=datetime.now(timezone.utc).isoformat()
    with connection() as db:
        cur=db.execute("""INSERT INTO evaluations
        (question,answer,retrieved_documents,answer_relevance,faithfulness,context_precision,completeness,overall_score,verdict,reasoning,issues,latency_ms,model,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (question,answer,json.dumps(retrieved_documents),evaluation["answer_relevance"],evaluation["faithfulness"],
         evaluation["context_precision"],evaluation["completeness"],evaluation["overall_score"],evaluation["verdict"],
         evaluation["reasoning"],json.dumps(evaluation.get("issues",[])),latency_ms,model,now))
        return cur.lastrowid

def list_evaluations(limit=20):
    with connection() as db:
        rows=db.execute("""SELECT id,question,answer,retrieved_documents,answer_relevance,faithfulness,
        context_precision,completeness,overall_score,verdict,reasoning,issues,latency_ms,model,created_at
        FROM evaluations ORDER BY id DESC LIMIT ?""",(limit,)).fetchall()
    keys=["id","question","answer","retrieved_documents","answer_relevance","faithfulness","context_precision",
          "completeness","overall_score","verdict","reasoning","issues","latency_ms","model","created_at"]
    result=[]
    for r in rows:
        item=dict(zip(keys,r))
        item["retrieved_documents"]=json.loads(item["retrieved_documents"])
        item["issues"]=json.loads(item["issues"])
        result.append(item)
    return result

def get_evaluation(evaluation_id):
    with connection() as db:
        row=db.execute("""SELECT id,question,answer,retrieved_documents,answer_relevance,faithfulness,
        context_precision,completeness,overall_score,verdict,reasoning,issues,latency_ms,model,created_at
        FROM evaluations WHERE id=?""",(evaluation_id,)).fetchone()
    if not row: return None
    keys=["id","question","answer","retrieved_documents","answer_relevance","faithfulness","context_precision",
          "completeness","overall_score","verdict","reasoning","issues","latency_ms","model","created_at"]
    item=dict(zip(keys,row))
    item["retrieved_documents"]=json.loads(item["retrieved_documents"])
    item["issues"]=json.loads(item["issues"])
    return item

def stats():
    with connection() as db:
        docs=db.execute("SELECT COUNT(*),COALESCE(SUM(chunks),0) FROM documents WHERE status='indexed'").fetchone()
        ev=db.execute("SELECT COUNT(*),COALESCE(AVG(overall_score),0),COALESCE(AVG(faithfulness),0),COALESCE(AVG(latency_ms),0) FROM evaluations").fetchone()
    return {"documents":docs[0],"chunks":docs[1],"evaluations":ev[0],"average_score":round(ev[1]),"groundedness":round(ev[2]),"average_latency_ms":round(ev[3])}
