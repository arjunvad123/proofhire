"""Main entry point for the grader.

Usage: python -m grader --run-id <run_id>

The grader expects:
- /sim directory: Contains the simulation template (app/, tests/, etc.)
- /workspace/submission/code.py: Candidate's submitted code
- /workspace/submission/writeup.md: Candidate's writeup

The grader outputs to /workspace/output/:
- metrics.json: Test results, coverage, timing metrics
- testlog.txt: Raw test output
- coverage.xml: Coverage report in Cobertura format
- diff.patch: Diff showing candidate changes
- grader_output.json: Detailed grader results
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="ProofHire Simulation Grader")
    parser.add_argument("--run-id", required=True, help="Unique run identifier")
    args = parser.parse_args()

    run_id = args.run_id
    start_time = time.time()

    print(f"[grader] Starting grading for run {run_id}")
    print(f"[grader] Python version: {sys.version}")
    print(f"[grader] Working directory: {os.getcwd()}")

    # Paths
    sim_dir = Path("/sim")
    submission_dir = Path("/workspace/submission")
    output_dir = Path("/workspace/output")
    work_dir = Path("/workspace/work")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "run_id": run_id,
        "started_at": datetime.utcnow().isoformat(),
        "success": False,
        "metrics": {},
        "errors": [],
    }

    try:
        # 1. Copy simulation template to work directory
        print("[grader] Setting up simulation environment...")
        if sim_dir.exists():
            shutil.copytree(sim_dir, work_dir, dirs_exist_ok=True)
            print(f"[grader] Copied simulation from {sim_dir}")
        else:
            results["errors"].append(f"Simulation directory not found: {sim_dir}")
            raise FileNotFoundError(f"Simulation directory not found: {sim_dir}")

        # 2. Apply candidate code
        print("[grader] Applying candidate code...")
        candidate_code_path = submission_dir / "code.py"
        if candidate_code_path.exists():
            # Read candidate code
            candidate_code = candidate_code_path.read_text()

            # Find the target file in the simulation (usually app/*.py)
            # For bugfix_v1, we replace app/rate_limiter.py
            target_files = list((work_dir / "app").glob("*.py"))
            if target_files:
                # Create diff before applying
                original_content = target_files[0].read_text()
                create_diff(original_content, candidate_code, target_files[0].name, output_dir)

                # Apply candidate code
                target_files[0].write_text(candidate_code)
                print(f"[grader] Applied code to {target_files[0]}")

                results["metrics"]["code_applied"] = True
            else:
                results["errors"].append("No target file found to apply code")
                results["metrics"]["code_applied"] = False
        else:
            results["errors"].append("Candidate code not found")
            results["metrics"]["code_applied"] = False

        # 3. Install simulation requirements if present
        requirements_file = work_dir / "requirements.txt"
        if requirements_file.exists():
            print("[grader] Installing requirements...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements_file)],
                cwd=str(work_dir),
                capture_output=True,
            )

        # 4. Run tests with coverage
        print("[grader] Running tests...")
        test_start = time.time()

        # Change to work directory for imports to work
        os.chdir(work_dir)
        sys.path.insert(0, str(work_dir))

        test_result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                "tests/",
                "-v",
                "--tb=short",
                "--cov=app",
                "--cov-report=xml",
                "--json-report",
                "--json-report-file=/workspace/output/pytest_report.json",
            ],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for tests
        )

        test_duration = time.time() - test_start

        # Save test log
        testlog = f"STDOUT:\n{test_result.stdout}\n\nSTDERR:\n{test_result.stderr}"
        (output_dir / "testlog.txt").write_text(testlog)
        print(f"[grader] Test output saved to testlog.txt")

        # Copy coverage report if generated
        coverage_file = work_dir / "coverage.xml"
        if coverage_file.exists():
            shutil.copy(coverage_file, output_dir / "coverage.xml")
            print("[grader] Coverage report saved")

        # Parse test results
        results["metrics"]["tests_passed"] = test_result.returncode == 0
        results["metrics"]["test_duration_seconds"] = test_duration
        results["metrics"]["exit_code"] = test_result.returncode

        # Parse pytest JSON report if available
        pytest_report_path = output_dir / "pytest_report.json"
        if pytest_report_path.exists():
            with open(pytest_report_path) as f:
                pytest_report = json.load(f)
                summary = pytest_report.get("summary", {})
                results["metrics"]["total_tests"] = summary.get("total", 0)
                results["metrics"]["passed_tests"] = summary.get("passed", 0)
                results["metrics"]["failed_tests_count"] = summary.get("failed", 0)
                results["metrics"]["skipped_tests"] = summary.get("skipped", 0)

        # Parse coverage
        coverage_percent = parse_coverage(output_dir / "coverage.xml")
        if coverage_percent is not None:
            results["metrics"]["coverage_percent"] = coverage_percent

        # 5. Analyze candidate code for metrics
        if candidate_code_path.exists():
            code_metrics = analyze_code(candidate_code_path.read_text())
            results["metrics"].update(code_metrics)

        # 6. Check if candidate added tests
        results["metrics"]["test_added"] = check_test_added(
            sim_dir / "tests",
            work_dir / "tests",
        )

        # Calculate time to green
        results["metrics"]["time_to_green_seconds"] = time.time() - start_time

        # Mark success
        results["success"] = results["metrics"].get("tests_passed", False)

    except subprocess.TimeoutExpired:
        results["errors"].append("Test execution timed out")
        results["metrics"]["timed_out"] = True

    except Exception as e:
        results["errors"].append(str(e))
        print(f"[grader] Error: {e}")

    finally:
        # Calculate total duration
        results["finished_at"] = datetime.utcnow().isoformat()
        results["duration_seconds"] = time.time() - start_time

        # Write output files
        print("[grader] Writing output files...")

        # metrics.json - simplified metrics for the runner
        metrics_output = {
            "tests_passed": results["metrics"].get("tests_passed", False),
            "failed_tests_count": results["metrics"].get("failed_tests_count", 0),
            "total_tests": results["metrics"].get("total_tests", 0),
            "coverage_percent": results["metrics"].get("coverage_percent", 0),
            "time_to_green_seconds": results["metrics"].get("time_to_green_seconds", 0),
            "test_added": results["metrics"].get("test_added", False),
        }
        (output_dir / "metrics.json").write_text(json.dumps(metrics_output, indent=2))

        # grader_output.json - full grader results
        (output_dir / "grader_output.json").write_text(json.dumps(results, indent=2))

        print(f"[grader] Grading complete. Success: {results['success']}")
        print(f"[grader] Metrics: {json.dumps(metrics_output, indent=2)}")

        # Exit with appropriate code
        sys.exit(0 if results["success"] else 1)


def create_diff(original: str, modified: str, filename: str, output_dir: Path) -> None:
    """Create a unified diff between original and modified content."""
    import difflib

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )

    diff_content = "".join(diff)
    (output_dir / "diff.patch").write_text(diff_content)


def parse_coverage(coverage_file: Path) -> float | None:
    """Parse coverage percentage from Cobertura XML."""
    if not coverage_file.exists():
        return None

    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        line_rate = root.get("line-rate")
        if line_rate:
            return float(line_rate) * 100
    except Exception:
        pass

    return None


def analyze_code(code: str) -> dict:
    """Analyze candidate code for simple metrics."""
    lines = code.split("\n")

    return {
        "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith("#")]),
        "comment_lines": len([l for l in lines if l.strip().startswith("#")]),
        "blank_lines": len([l for l in lines if not l.strip()]),
    }


def check_test_added(original_tests: Path, new_tests: Path) -> bool:
    """Check if candidate added any new test files or test functions."""
    # Simple heuristic: check if test directory has more content
    if not original_tests.exists() or not new_tests.exists():
        return False

    original_count = len(list(original_tests.glob("**/*.py")))
    new_count = len(list(new_tests.glob("**/*.py")))

    return new_count > original_count


if __name__ == "__main__":
    main()
