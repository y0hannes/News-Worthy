# Use an official Python base image
FROM python:3.13-slim

# Create a non‑root user for security
RUN useradd -m appuser
WORKDIR /app

# Copy dependency file first (optimizes caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code
COPY app/ ./

# Switch to non‑root user
USER appuser

# Command that runs when the container starts
CMD ["python", "main.py"]
