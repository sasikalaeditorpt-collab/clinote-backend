# Use a slim Python base image
FROM python:3.11-slim

# Install system dependencies including LibreOffice
RUN apt-get update && \
    apt-get install -y libreoffice && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose the port Render expects
EXPOSE 10000

# Start the FastAPI app
CMD ["uvicorn", "typing_engine_api:app", "--host", "0.0.0.0", "--port", "10000"]
