# Universal Dockerfile for MovieRec AI Platform (Hugging Face Spaces & Cloud Containers)
FROM python:3.10-slim

# Prevent Python from writing bytecode and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HOME=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first (compact CPU build avoids heavy CUDA bloat)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy and install python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application assets and code
COPY . /app

# Ensure proper permissions inside the container
RUN chmod -R 777 /app

# Expose default Hugging Face Space port
EXPOSE 7860

# Start FastAPI Uvicorn server (serving API, WebSockets, and mounted static frontend)
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
