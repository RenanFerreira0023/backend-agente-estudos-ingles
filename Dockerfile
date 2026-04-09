# Use a lightweight Python 3.11 base image
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app

# Install system dependencies (needed for GPT4All's underlying libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to take advantage of Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
# We'll ignore large model files via .dockerignore to keep the image slim
COPY . .

# Ensure models directory exists
RUN mkdir -p /app/models

# Expose the API port (as defined in api.py)
EXPOSE 8000

# Command to run the application
# api.py starts uvicorn on 0.0.0.0:8000
CMD ["python", "api.py"]
