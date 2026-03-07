FROM python:3.12-slim

WORKDIR /app

# Install build deps needed by some ChromaDB / sentence-transformers deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-cache friendly)
# Install deps explicitly so we don't need source code at this stage.
RUN pip install --no-cache-dir \
    "fastmcp>=2.0" \
    "chromadb>=0.5" \
    "sentence-transformers>=3.0" \
    "pydantic>=2.0"

# Pre-download the sentence-transformers model into the image so the first
# container start is instant.  The model lives at /app/models (not a volume).
ENV SENTENCE_TRANSFORMERS_HOME=/app/models
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application source
COPY app/ app/

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["fastmcp", "run", "app/main.py", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
