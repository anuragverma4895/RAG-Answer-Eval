import re
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

def clean_text(text):
    text=re.sub(r"\r\n?", "\n", text)
    text=re.sub(r"[ \t]+", " ", text)
    text=re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    text=clean_text(text)
    if not text: return []
    chunks=[]
    start=0
    while start < len(text):
        end=min(len(text), start+chunk_size)
        if end < len(text):
            boundary=max(text.rfind("\n",start,end), text.rfind(". ",start,end))
            if boundary > start+chunk_size//2:
                end=boundary+1
        piece=text[start:end].strip()
        if piece: chunks.append(piece)
        if end>=len(text): break
        start=max(end-overlap,start+1)
    return chunks
