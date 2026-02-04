"""Docker sandbox for secure simulation execution.

The sandbox ensures:
- No network access (isolated)
- Resource limits (CPU, memory)
- Timeout enforcement
- Clean workspace per run
"""

import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import docker
import structlog

from runner.config import RunnerConfig

logger = structlog.get_logger(__name__)


@dataclass
class SandboxResult:
    """Result from sandbox execution."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    artifacts: dict[str, str]  # name -> local path
    error: str | None = None


class SandboxManager:
    """Manages Docker sandboxes for simulation execution."""

    def __init__(self, config: RunnerConfig):
        self.config = config
        self.docker_client = docker.from_env()

    def execute(
        self,
        simulation_id: str,
        candidate_code: str,
        candidate_writeup: str,
        run_id: str,
    ) -> SandboxResult:
        """Execute a simulation in an isolated sandbox.

        Args:
            simulation_id: ID of the simulation to run (e.g., "bugfix_v1")
            candidate_code: The candidate's submitted code/diff
            candidate_writeup: The candidate's writeup text
            run_id: Unique identifier for this run

        Returns:
            SandboxResult with outputs and artifacts
        """
        start_time = time.time()
        workspace = None

        try:
            # Create temporary workspace
            workspace = self._create_workspace(
                simulation_id=simulation_id,
                candidate_code=candidate_code,
                candidate_writeup=candidate_writeup,
                run_id=run_id,
            )

            logger.info(
                "Starting sandbox execution",
                run_id=run_id,
                simulation_id=simulation_id,
                workspace=str(workspace),
            )

            # Run the container
            container = self.docker_client.containers.run(
                image=self.config.sandbox_image,
                command=["python", "-m", "grader", "--run-id", run_id],
                volumes={
                    str(workspace): {"bind": "/workspace", "mode": "rw"},
                    str(Path(self.config.sims_path) / simulation_id): {
                        "bind": "/sim",
                        "mode": "ro",
                    },
                },
                working_dir="/workspace",
                mem_limit=self.config.sandbox_memory_limit,
                cpu_period=100000,
                cpu_quota=int(self.config.sandbox_cpu_limit * 100000),
                network_disabled=self.config.sandbox_network_disabled,
                detach=True,
                remove=False,
            )

            # Wait for completion with timeout
            try:
                result = container.wait(timeout=self.config.sandbox_timeout)
                exit_code = result["StatusCode"]
            except Exception as e:
                logger.warning("Container timeout", run_id=run_id, error=str(e))
                container.kill()
                return SandboxResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="",
                    duration_seconds=time.time() - start_time,
                    artifacts={},
                    error="Execution timed out",
                )

            # Collect logs
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            # Collect artifacts from workspace
            artifacts = self._collect_artifacts(workspace)

            # Cleanup container
            container.remove()

            duration = time.time() - start_time
            success = exit_code == 0

            logger.info(
                "Sandbox execution complete",
                run_id=run_id,
                success=success,
                exit_code=exit_code,
                duration_seconds=duration,
                artifact_count=len(artifacts),
            )

            return SandboxResult(
                success=success,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                artifacts=artifacts,
            )

        except docker.errors.ImageNotFound:
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration_seconds=time.time() - start_time,
                artifacts={},
                error=f"Sandbox image not found: {self.config.sandbox_image}",
            )

        except Exception as e:
            logger.exception("Sandbox execution failed", run_id=run_id, error=str(e))
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration_seconds=time.time() - start_time,
                artifacts={},
                error=str(e),
            )

        finally:
            # Cleanup workspace
            if workspace and workspace.exists():
                shutil.rmtree(workspace, ignore_errors=True)

    def _create_workspace(
        self,
        simulation_id: str,
        candidate_code: str,
        candidate_writeup: str,
        run_id: str,
    ) -> Path:
        """Create isolated workspace with candidate submissions."""
        workspace = Path(tempfile.mkdtemp(prefix=f"proofhire-{run_id}-"))

        # Copy simulation template
        sim_path = Path(self.config.sims_path) / simulation_id
        if sim_path.exists():
            shutil.copytree(sim_path, workspace / "sim", dirs_exist_ok=True)

        # Write candidate code
        code_path = workspace / "submission" / "code.py"
        code_path.parent.mkdir(parents=True, exist_ok=True)
        code_path.write_text(candidate_code)

        # Write candidate writeup
        writeup_path = workspace / "submission" / "writeup.md"
        writeup_path.write_text(candidate_writeup)

        # Create output directory for artifacts
        (workspace / "output").mkdir(exist_ok=True)

        return workspace

    def _collect_artifacts(self, workspace: Path) -> dict[str, str]:
        """Collect generated artifacts from workspace."""
        artifacts = {}
        output_dir = workspace / "output"

        if not output_dir.exists():
            return artifacts

        # Expected artifact files
        artifact_files = [
            "metrics.json",
            "testlog.txt",
            "coverage.xml",
            "diff.patch",
            "grader_output.json",
        ]

        for filename in artifact_files:
            filepath = output_dir / filename
            if filepath.exists():
                artifacts[filename] = str(filepath)

        return artifacts

    def build_sandbox_image(self) -> bool:
        """Build the sandbox Docker image."""
        try:
            dockerfile_path = Path(__file__).parent / "sandbox" / "Dockerfile"
            if not dockerfile_path.exists():
                logger.error("Sandbox Dockerfile not found")
                return False

            self.docker_client.images.build(
                path=str(dockerfile_path.parent),
                tag=self.config.sandbox_image,
                rm=True,
            )
            logger.info("Sandbox image built", tag=self.config.sandbox_image)
            return True

        except Exception as e:
            logger.exception("Failed to build sandbox image", error=str(e))
            return False
