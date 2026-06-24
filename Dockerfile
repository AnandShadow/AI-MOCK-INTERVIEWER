# Use official Python runtime as a parent image (Slim variant for smaller footprint)
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app

# Install system dependencies required for Edge-TTS and audio processing
# ffmpeg is required to parse and generate complex audio formats
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies with strict versioning
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the standard Streamlit port
EXPOSE 8501

# Add a healthcheck to ensure the container is routing correctly
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Command to run the Streamlit app
# We explicitly bind to 0.0.0.0 and disable CORS/XSRF to allow cloud load balancers to route WebSocket traffic seamlessly
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
