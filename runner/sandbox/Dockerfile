FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python testing tools
RUN pip install --no-cache-dir \
    pytest==7.4.3 \
    pytest-cov==4.1.0 \
    pytest-json-report==1.5.0 \
    coverage==7.3.2

# Copy grader package under a parent import path.
COPY grader/ /grader/grader/

# Set Python path
ENV PYTHONPATH=/grader:/workspace/sim:/workspace

# Create non-root user for security
RUN useradd -m -s /bin/bash sandbox
USER sandbox

# Working directory
WORKDIR /workspace

# Entry point
ENTRYPOINT ["python", "-m", "grader"]
