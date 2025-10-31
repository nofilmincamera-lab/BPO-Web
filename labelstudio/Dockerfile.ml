FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY labelstudio/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Install the project
RUN pip install -e .

# Expose ML backend port
EXPOSE 9090

# Set environment variables
ENV PYTHONPATH=/app
ENV LABEL_STUDIO_ML_BACKEND_V2=true

# Run the ML backend
CMD ["python", "labelstudio/ml_backend_config.py"]

