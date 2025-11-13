FROM python:3.11-slim

# Avoid warnings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Install system deps for building / html parsing (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libxml2-dev libxslt-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project
COPY . /app

# Ensure permissions
RUN chown -R appuser:appgroup /app

USER appuser

# Expose port for FastAPI
EXPOSE 8000

# Default command: run uvicorn for the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
