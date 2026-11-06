FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user and switch to it
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

# Cloud Run sets PORT env var; default to 8000 for local dev
ENV PORT=8000
EXPOSE ${PORT}

# Run the application on the port Cloud Run provides
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
