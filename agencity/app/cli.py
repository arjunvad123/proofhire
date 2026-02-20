"""
Agencity terminal CLI MVP.

Usage examples:
  agencity doctor
  agencity search --company-id <uuid> --role-title "Founding Engineer" --required-skills Python React
  agencity daemon --company-id <uuid> --role-title "Founding Engineer" --interval-seconds 900
  agencity serve-api --port 8001
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
import uvicorn

from app.config import settings
from app.services.master_orchestrator import master_orchestrator


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, default=str))


@dataclass
class DaemonState:
    running: bool = True
    iteration: int = 0
    last_run_at: str | None = None
    last_error: str | None = None


def _validate_required_values(values: dict[str, str]) -> list[str]:
    missing = []
    for key, value in values.items():
        if not value:
            missing.append(key)
    return missing


def cmd_doctor(_: argparse.Namespace) -> int:
    checks: dict[str, Any] = {
        "timestamp": _utc_now_iso(),
        "environment": settings.app_env,
        "checks": {},
    }

    api_base = os.getenv("AGENCITY_API_BASE", "http://localhost:8001")
    try:
        response = httpx.get(f"{api_base}/health", timeout=5.0)
        checks["checks"]["backend_health"] = {
            "ok": response.status_code == 200,
            "status_code": response.status_code,
        }
    except Exception as exc:  # pragma: no cover - best effort
        checks["checks"]["backend_health"] = {"ok": False, "error": str(exc)}

    missing = _validate_required_values(
        {
            "SUPABASE_URL": settings.supabase_url,
            "SUPABASE_KEY": settings.supabase_key,
            "ANTHROPIC_API_KEY": settings.anthropic_api_key,
            "PERPLEXITY_API_KEY": settings.perplexity_api_key,
            "PDL_API_KEY": settings.pdl_api_key,
            "CLADO_API_KEY": settings.clado_api_key,
        }
    )
    checks["checks"]["config"] = {"ok": len(missing) == 0, "missing": missing}
    checks["ok"] = all(v.get("ok") for v in checks["checks"].values())

    _print_json(checks)
    return 0 if checks["ok"] else 1


async def _run_search(args: argparse.Namespace) -> dict[str, Any]:
    result = await master_orchestrator.search(
        company_id=args.company_id,
        role_title=args.role_title,
        required_skills=args.required_skills,
        preferred_skills=args.preferred_skills,
        location=args.location,
        years_experience=args.years_experience,
        mode=args.mode,
        include_external=args.include_external,
        include_timing=args.include_timing,
        deep_research=args.deep_research,
        limit=args.limit,
    )

    top_candidates = []
    for c in result.search_result.candidates[: min(5, len(result.search_result.candidates))]:
        top_candidates.append(
            {
                "id": c.id,
                "name": c.full_name,
                "title": c.current_title,
                "company": c.current_company,
                "combined_score": round(c.combined_score, 2),
                "tier": c.tier,
                "timing_urgency": c.timing_urgency,
                "why_consider": c.why_consider[:2],
            }
        )

    return {
        "timestamp": _utc_now_iso(),
        "mode": result.mode,
        "duration_seconds": result.total_duration_seconds,
        "features_used": result.features_used,
        "search_summary": {
            "role_title": result.search_result.role_title,
            "total_found": result.search_result.total_found,
            "returned": len(result.search_result.candidates),
            "tier_1": result.search_result.tier_1_count,
            "tier_2": result.search_result.tier_2_count,
            "tier_3": result.search_result.tier_3_count,
            "high_urgency": result.search_result.high_urgency_count,
        },
        "top_candidates": top_candidates,
    }


def cmd_search(args: argparse.Namespace) -> int:
    payload = asyncio.run(_run_search(args))
    _print_json(payload)
    return 0


def cmd_serve_api(args: argparse.Namespace) -> int:
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def cmd_daemon(args: argparse.Namespace) -> int:
    state = DaemonState()

    def _stop_handler(signum: int, _: Any) -> None:
        state.running = False
        print(f"received_signal={signum} shutting_down=true")

    signal.signal(signal.SIGINT, _stop_handler)
    signal.signal(signal.SIGTERM, _stop_handler)

    print(
        json.dumps(
            {
                "event": "daemon_started",
                "timestamp": _utc_now_iso(),
                "company_id": args.company_id,
                "role_title": args.role_title,
                "interval_seconds": args.interval_seconds,
            }
        )
    )

    while state.running:
        state.iteration += 1
        state.last_run_at = _utc_now_iso()
        try:
            payload = asyncio.run(_run_search(args))
            payload["event"] = "daemon_iteration_complete"
            payload["iteration"] = state.iteration
            print(json.dumps(payload, default=str))
            state.last_error = None
        except Exception as exc:  # pragma: no cover - runtime safety
            state.last_error = str(exc)
            print(
                json.dumps(
                    {
                        "event": "daemon_iteration_failed",
                        "timestamp": _utc_now_iso(),
                        "iteration": state.iteration,
                        "error": state.last_error,
                    }
                )
            )

        slept = 0
        while state.running and slept < args.interval_seconds:
            time.sleep(1)
            slept += 1

    print(
        json.dumps(
            {
                "event": "daemon_stopped",
                "timestamp": _utc_now_iso(),
                "iterations": state.iteration,
                "last_run_at": state.last_run_at,
                "last_error": state.last_error,
            }
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agencity", description="Agencity terminal MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Run environment and health checks")
    p_doctor.set_defaults(func=cmd_doctor)

    # search
    p_search = subparsers.add_parser("search", help="Run end-to-end orchestrated search")
    p_search.add_argument("--company-id", required=True, help="Company UUID")
    p_search.add_argument("--role-title", required=True, help="Role title")
    p_search.add_argument("--required-skills", nargs="*", default=[], help="Must-have skills")
    p_search.add_argument("--preferred-skills", nargs="*", default=[], help="Nice-to-have skills")
    p_search.add_argument("--location", default=None, help="Preferred location")
    p_search.add_argument("--years-experience", type=int, default=None, help="Minimum years experience")
    p_search.add_argument("--mode", choices=["network_only", "quick", "full"], default="quick")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.add_argument("--include-external", action=argparse.BooleanOptionalAction, default=True)
    p_search.add_argument("--include-timing", action=argparse.BooleanOptionalAction, default=True)
    p_search.add_argument("--deep-research", action=argparse.BooleanOptionalAction, default=False)
    p_search.set_defaults(func=cmd_search)

    # daemon
    p_daemon = subparsers.add_parser("daemon", help="Run scheduled orchestrated searches")
    p_daemon.add_argument("--company-id", required=True, help="Company UUID")
    p_daemon.add_argument("--role-title", required=True, help="Role title")
    p_daemon.add_argument("--required-skills", nargs="*", default=[], help="Must-have skills")
    p_daemon.add_argument("--preferred-skills", nargs="*", default=[], help="Nice-to-have skills")
    p_daemon.add_argument("--location", default=None, help="Preferred location")
    p_daemon.add_argument("--years-experience", type=int, default=None, help="Minimum years experience")
    p_daemon.add_argument("--mode", choices=["network_only", "quick", "full"], default="quick")
    p_daemon.add_argument("--limit", type=int, default=10)
    p_daemon.add_argument("--include-external", action=argparse.BooleanOptionalAction, default=True)
    p_daemon.add_argument("--include-timing", action=argparse.BooleanOptionalAction, default=True)
    p_daemon.add_argument("--deep-research", action=argparse.BooleanOptionalAction, default=False)
    p_daemon.add_argument("--interval-seconds", type=int, default=900, help="Loop interval")
    p_daemon.set_defaults(func=cmd_daemon)

    # serve-api
    p_api = subparsers.add_parser("serve-api", help="Run Agencity FastAPI server")
    p_api.add_argument("--host", default="0.0.0.0")
    p_api.add_argument("--port", type=int, default=8001)
    p_api.add_argument("--reload", action=argparse.BooleanOptionalAction, default=True)
    p_api.set_defaults(func=cmd_serve_api)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
