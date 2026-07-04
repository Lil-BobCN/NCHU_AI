FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app
ENV XDG_CACHE_HOME=/app/.cache
ENV PADDLE_PDX_CACHE_HOME=/app/.cache/paddlex
ENV PADDLE_HOME=/app/.cache/paddle
ENV HF_HOME=/app/.cache/huggingface
ENV MODELSCOPE_CACHE=/app/.cache/modelscope
ENV PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True
ENV WEB_CONCURRENCY=4

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libreoffice-calc \
        libreoffice-writer \
        libgl1 \
        fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY sql /app/sql
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

RUN mkdir -p /app/.cache/paddlex /app/.cache/paddle /app/.cache/huggingface /app/.cache/modelscope \
    && python -c "from app.services.ocr_service import PaddleOcrService; PaddleOcrService(lang='ch', use_gpu=False)._get_engine()"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-4}"]
