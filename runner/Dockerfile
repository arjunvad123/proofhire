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

# Copy runner code
COPY . .

# Create non-root user for security
RUN useradd -m -s /bin/bash runner
USER runner

CMD ["python", "-m", "runner"]
