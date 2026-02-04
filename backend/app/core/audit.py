"""Audit logging utilities."""

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hashing import hash_chain, hash_json
from app.core.ids import generate_id
from app.core.time import utc_now
from app.logging_config import get_logger

logger = get_logger(__name__)


class AuditLogger:
    """Append-only audit log with hash chain integrity."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._last_hash: str | None = None

    async def log(
        self,
        event_type: str,
        event_data: dict[str, Any],
        org_id: str | None = None,
        actor_user_id: str | None = None,
    ) -> str:
        """Log an event to the audit trail.

        Returns the event ID.
        """
        from app.db.models import AuditLog

        event_id = generate_id()
        event_json = json.dumps(event_data, sort_keys=True)

        # Get previous hash for chain
        if self._last_hash is None:
            # Query the last hash from DB
            result = await self.db.execute(
                AuditLog.__table__.select()
                .order_by(AuditLog.created_at.desc())
                .limit(1)
            )
            last_entry = result.first()
            self._last_hash = last_entry.event_hash if last_entry else "genesis"

        # Compute new hash
        event_hash = hash_chain(self._last_hash, event_json)

        audit_entry = AuditLog(
            id=event_id,
            org_id=org_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            event_json=event_data,
            prev_hash=self._last_hash,
            event_hash=event_hash,
            created_at=utc_now(),
        )

        self.db.add(audit_entry)
        self._last_hash = event_hash

        logger.info(
            "Audit event logged",
            event_id=event_id,
            event_type=event_type,
            org_id=org_id,
            actor_user_id=actor_user_id,
        )

        return event_id


async def create_audit_logger(db: AsyncSession) -> AuditLogger:
    """Create an audit logger instance."""
    return AuditLogger(db)
