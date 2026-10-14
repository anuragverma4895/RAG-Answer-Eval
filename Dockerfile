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
    HF_HOME=/var/data/huggingface \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=1

WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
# Install the CPU wheel explicitly: Render instances do not have an NVIDIA GPU.
# This avoids pulling the large CUDA/NVIDIA dependency stack into the runtime image.
RUN python -m pip install --upgrade pip \
    && python -m pip install --index-url https://download.pytorch.org/whl/cpu torch \
    && python -m pip install -r requirements.txt

COPY backend/app ./app
COPY --from=frontend-build /workspace/frontend/dist ./static

EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --log-level info"]
