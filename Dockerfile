# Use Railway's recommended Python base image
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on \
    PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies (add any required packages here)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv --copies /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Set PATH to include virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Set Railway-specific port (optional but recommended)
ENV PORT=8000
EXPOSE $PORT

# Add your startup command (replace with your actual command)
CMD ["gunicorn", "your_project.wsgi", "--bind", "0.0.0.0:$PORT"]
