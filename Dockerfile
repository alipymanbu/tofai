FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make PORT configurable via environment variable with default fallback
# Don't hardcode the port - Cloud Run wants to control this
ENV PORT=${PORT:-8000}

# Expose the dynamic port
EXPOSE ${PORT}

# Command to run the application with the dynamic port
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 4"]