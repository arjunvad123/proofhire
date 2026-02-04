"""Runner configuration."""

import os
from dataclasses import dataclass


@dataclass
class RunnerConfig:
    """Configuration for the runner service."""

    # Redis
    redis_url: str
    job_queue: str = "simulation_jobs"
    poll_timeout: int = 5

    # S3/MinIO
    s3_endpoint: str = ""
    s3_bucket: str = "proofhire-artifacts"
    s3_access_key: str = ""
    s3_secret_key: str = ""

    # Backend API (for callbacks)
    backend_url: str = "http://backend:8000"
    backend_api_key: str = ""

    # Sandbox settings
    sandbox_image: str = "proofhire-sandbox:latest"
    sandbox_timeout: int = 600  # 10 minutes
    sandbox_memory_limit: str = "512m"
    sandbox_cpu_limit: float = 1.0
    sandbox_network_disabled: bool = True

    # Worker identity
    worker_id: str = ""

    # Simulation repos path
    sims_path: str = "/app/sims"

    @classmethod
    def from_env(cls) -> "RunnerConfig":
        """Load configuration from environment variables."""
        return cls(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            job_queue=os.getenv("JOB_QUEUE", "simulation_jobs"),
            poll_timeout=int(os.getenv("POLL_TIMEOUT", "5")),
            s3_endpoint=os.getenv("S3_ENDPOINT", "http://minio:9000"),
            s3_bucket=os.getenv("S3_BUCKET", "proofhire-artifacts"),
            s3_access_key=os.getenv("S3_ACCESS_KEY", "minioadmin"),
            s3_secret_key=os.getenv("S3_SECRET_KEY", "minioadmin"),
            backend_url=os.getenv("BACKEND_URL", "http://backend:8000"),
            backend_api_key=os.getenv("BACKEND_API_KEY", ""),
            sandbox_image=os.getenv("SANDBOX_IMAGE", "proofhire-sandbox:latest"),
            sandbox_timeout=int(os.getenv("SANDBOX_TIMEOUT", "600")),
            sandbox_memory_limit=os.getenv("SANDBOX_MEMORY_LIMIT", "512m"),
            sandbox_cpu_limit=float(os.getenv("SANDBOX_CPU_LIMIT", "1.0")),
            sandbox_network_disabled=os.getenv("SANDBOX_NETWORK_DISABLED", "true").lower() == "true",
            worker_id=os.getenv("WORKER_ID", f"worker-{os.getpid()}"),
            sims_path=os.getenv("SIMS_PATH", "/app/sims"),
        )
