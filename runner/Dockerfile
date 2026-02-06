FROM python:3.11-slim

# Install Docker CLI for sandbox management
RUN apt-get update && apt-get install -y \
    docker.io \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy runner code into a package directory
COPY . ./runner/

# Note: Running as root to access Docker socket
# In production, use a proper Docker group setup

CMD ["python", "-m", "runner"]
