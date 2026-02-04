"""Main runner worker loop.

Pulls simulation jobs from Redis queue and executes them in Docker sandboxes.
"""

import os
import signal
import sys
import time
from typing import Any

import redis
import structlog

from runner.config import RunnerConfig
from runner.job_handlers import handle_simulation_job
from runner.sandbox import SandboxManager

logger = structlog.get_logger(__name__)


class Runner:
    """Main runner service that processes simulation jobs."""

    def __init__(self, config: RunnerConfig):
        self.config = config
        self.redis = redis.Redis.from_url(config.redis_url, decode_responses=True)
        self.sandbox_manager = SandboxManager(config)
        self._running = True

    def run(self) -> None:
        """Main worker loop - pull jobs and execute."""
        logger.info("Runner started", worker_id=self.config.worker_id)

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        while self._running:
            try:
                self._process_next_job()
            except redis.ConnectionError as e:
                logger.error("Redis connection error", error=str(e))
                time.sleep(5)
            except Exception as e:
                logger.exception("Unexpected error in worker loop", error=str(e))
                time.sleep(1)

        logger.info("Runner shutdown complete")

    def _process_next_job(self) -> None:
        """Pull and process the next job from queue."""
        # Blocking pop with timeout
        result = self.redis.brpop(
            self.config.job_queue,
            timeout=self.config.poll_timeout,
        )

        if result is None:
            # Timeout - no job available
            return

        queue_name, job_data = result

        try:
            import json
            job = json.loads(job_data)
            run_id = job.get("run_id")

            logger.info("Processing job", run_id=run_id, job_type=job.get("type"))

            # Update job status
            self._update_status(run_id, "running")

            # Execute the job
            result = handle_simulation_job(
                job=job,
                sandbox_manager=self.sandbox_manager,
                config=self.config,
            )

            # Update final status
            if result.get("success"):
                self._update_status(run_id, "completed", result)
                logger.info("Job completed successfully", run_id=run_id)
            else:
                self._update_status(run_id, "failed", result)
                logger.warning("Job failed", run_id=run_id, error=result.get("error"))

        except Exception as e:
            logger.exception("Error processing job", error=str(e))
            if "run_id" in job:
                self._update_status(job["run_id"], "failed", {"error": str(e)})

    def _update_status(
        self,
        run_id: str,
        status: str,
        result: dict[str, Any] | None = None,
    ) -> None:
        """Update job status in Redis for backend to poll."""
        import json

        status_data = {
            "run_id": run_id,
            "status": status,
            "updated_at": time.time(),
        }
        if result:
            status_data["result"] = result

        self.redis.hset(
            f"run:{run_id}",
            mapping={"status": json.dumps(status_data)},
        )

        # Also notify backend via pub/sub
        self.redis.publish(
            "run_updates",
            json.dumps({"run_id": run_id, "status": status}),
        )

    def _handle_shutdown(self, signum: int, frame: Any) -> None:
        """Handle graceful shutdown."""
        logger.info("Shutdown signal received", signal=signum)
        self._running = False


def main() -> None:
    """Entry point."""
    config = RunnerConfig.from_env()

    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    runner = Runner(config)
    runner.run()


if __name__ == "__main__":
    main()
