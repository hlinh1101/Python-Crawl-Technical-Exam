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

# Workdir inside container
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy whole project
COPY . /app

# Ensure data dir exists (optional nhưng đẹp)
RUN mkdir -p /app/data/html_backup && chown -R appuser:appgroup /app

USER appuser

# Expose port for FastAPI
EXPOSE 8000

# Run FastAPI app (main.py nằm trong folder app/)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
