"""Job handlers for different simulation types."""

import json
import time
from typing import Any

import boto3
import httpx
import structlog

if __package__ in (None, ""):
    # Support running from within the runner directory (python -m runner)
    from config import RunnerConfig
    from sandbox import SandboxManager, SandboxResult
else:
    from runner.config import RunnerConfig
    from runner.sandbox import SandboxManager, SandboxResult

logger = structlog.get_logger(__name__)


def handle_simulation_job(
    job: dict[str, Any],
    sandbox_manager: SandboxManager,
    config: RunnerConfig,
) -> dict[str, Any]:
    """Handle a simulation job.

    Job format:
    {
        "run_id": "run_xxx",
        "type": "simulation",
        "simulation_id": "bugfix_v1",
        "application_id": "app_xxx",
        "candidate_code": "...",
        "candidate_writeup": "...",
    }
    """
    run_id = job["run_id"]
    simulation_id = job["simulation_id"]

    logger.info(
        "Handling simulation job",
        run_id=run_id,
        simulation_id=simulation_id,
    )

    # Execute in sandbox
    sandbox_result = sandbox_manager.execute(
        simulation_id=simulation_id,
        candidate_code=job.get("candidate_code", ""),
        candidate_writeup=job.get("candidate_writeup", ""),
        run_id=run_id,
    )

    if not sandbox_result.success:
        # Always notify backend on failure so run state does not get stuck as "running".
        notify_backend(
            run_id=run_id,
            success=False,
            metrics={},
            artifact_urls={},
            duration_seconds=sandbox_result.duration_seconds,
            config=config,
        )
        return {
            "success": False,
            "error": sandbox_result.error or "Sandbox execution failed",
            "stdout": sandbox_result.stdout[:5000],  # Truncate
            "stderr": sandbox_result.stderr[:5000],
            "duration_seconds": sandbox_result.duration_seconds,
        }

    # Upload artifacts to S3
    artifact_urls = upload_artifacts(
        run_id=run_id,
        artifacts=sandbox_result.artifacts,
        config=config,
    )

    # Parse metrics from grader output
    metrics = parse_metrics(sandbox_result.artifacts)

    # Notify backend of completion
    notify_backend(
        run_id=run_id,
        success=True,
        metrics=metrics,
        artifact_urls=artifact_urls,
        duration_seconds=sandbox_result.duration_seconds,
        config=config,
    )

    return {
        "success": True,
        "metrics": metrics,
        "artifact_urls": artifact_urls,
        "duration_seconds": sandbox_result.duration_seconds,
    }


def upload_artifacts(
    run_id: str,
    artifacts: dict[str, str],
    config: RunnerConfig,
) -> dict[str, str]:
    """Upload artifacts to S3 and return URLs."""
    s3_client = boto3.client(
        "s3",
        endpoint_url=config.s3_endpoint,
        aws_access_key_id=config.s3_access_key,
        aws_secret_access_key=config.s3_secret_key,
    )

    urls = {}

    for name, local_path in artifacts.items():
        try:
            s3_key = f"runs/{run_id}/{name}"

            with open(local_path, "rb") as f:
                s3_client.upload_fileobj(
                    f,
                    config.s3_bucket,
                    s3_key,
                    ExtraArgs={"ContentType": _get_content_type(name)},
                )

            # Generate presigned URL
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": config.s3_bucket, "Key": s3_key},
                ExpiresIn=86400 * 7,  # 7 days
            )
            urls[name] = url

            logger.info("Uploaded artifact", run_id=run_id, name=name, key=s3_key)

        except Exception as e:
            logger.error("Failed to upload artifact", name=name, error=str(e))

    return urls


def parse_metrics(artifacts: dict[str, str]) -> dict[str, Any]:
    """Parse metrics from grader output."""
    metrics = {}

    # Try to read metrics.json
    if "metrics.json" in artifacts:
        try:
            with open(artifacts["metrics.json"]) as f:
                metrics = json.load(f)
        except Exception as e:
            logger.error("Failed to parse metrics.json", error=str(e))

    # Try to read grader_output.json for additional data
    if "grader_output.json" in artifacts:
        try:
            with open(artifacts["grader_output.json"]) as f:
                grader_output = json.load(f)
                # Merge grader metrics
                if "metrics" in grader_output:
                    metrics.update(grader_output["metrics"])
        except Exception as e:
            logger.error("Failed to parse grader_output.json", error=str(e))

    return metrics


def notify_backend(
    run_id: str,
    success: bool,
    metrics: dict[str, Any],
    artifact_urls: dict[str, str],
    duration_seconds: float,
    config: RunnerConfig,
) -> None:
    """Notify backend of job completion."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{config.backend_url}/api/internal/runs/{run_id}/complete",
                json={
                    "success": success,
                    "metrics": metrics,
                    "artifact_urls": artifact_urls,
                    "duration_seconds": duration_seconds,
                },
                headers={
                    "X-Internal-Key": config.backend_api_key,
                },
            )
            response.raise_for_status()
            logger.info("Backend notified", run_id=run_id)

    except Exception as e:
        logger.error("Failed to notify backend", run_id=run_id, error=str(e))


def _get_content_type(filename: str) -> str:
    """Get content type for artifact file."""
    if filename.endswith(".json"):
        return "application/json"
    elif filename.endswith(".xml"):
        return "application/xml"
    elif filename.endswith(".txt"):
        return "text/plain"
    elif filename.endswith(".patch"):
        return "text/x-diff"
    else:
        return "application/octet-stream"
