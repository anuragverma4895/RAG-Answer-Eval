# Build the React/Vite frontend first.
FROM node:22-alpine AS frontend-build
WORKDIR /workspace/frontend
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# One Python web process serves both the API and the compiled frontend.
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=1

WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
# Chroma's ONNX Runtime embedding function runs on CPU and avoids the
# large PyTorch/CUDA/NVIDIA stack in a CPU-only Render container.
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# Store Chroma's downloaded ONNX model on Render's persistent disk.
ENV HOME=/var/data/home

COPY backend/app ./app
COPY --from=frontend-build /workspace/frontend/dist ./static

EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --log-level info"]
