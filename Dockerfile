# Remote MCP server image for fly.io.
# Same engine as the local stdio connector; only the transport (HTTP) differs.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    GREYHAWK_MCP_DB=/data/campaign.db

WORKDIR /app

# Deps first for layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code.
COPY . .

# The SQLite campaign DB lives on a mounted Fly volume, not in the image.
RUN mkdir -p /data

EXPOSE 8080

CMD ["uvicorn", "server.http_server:app", "--host", "0.0.0.0", "--port", "8080"]
