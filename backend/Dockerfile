FROM python:3.10-slim

# System deps needed by opencv-python-headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Folders the app writes to at runtime (safe to recreate on every deploy)
RUN mkdir -p pipeline_data/uploads pipeline_data/outputs

# Render (and most PaaS) inject $PORT at runtime — default to 8000 for local/docker-compose use
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
