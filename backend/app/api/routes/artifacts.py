"""Artifact routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import boto3
from botocore.exceptions import ClientError

from app.config import get_settings
from app.db.session import get_db
from app.db.models import Artifact, SimulationRun, Application, Role, Membership
from app.deps import CurrentUser

router = APIRouter()
settings = get_settings()


def get_s3_client():
    """Get S3/MinIO client."""
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Download an artifact (authorized users only)."""
    result = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )

    # Get run, application, role to verify access
    result = await db.execute(
        select(SimulationRun).where(SimulationRun.id == artifact.simulation_run_id)
    )
    run = result.scalar_one_or_none()

    result = await db.execute(select(Application).where(Application.id == run.application_id))
    application = result.scalar_one_or_none()

    result = await db.execute(select(Role).where(Role.id == application.role_id))
    role = result.scalar_one_or_none()

    result = await db.execute(
        select(Membership)
        .where(Membership.org_id == role.org_id, Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download this artifact",
        )

    # Download from S3
    try:
        s3 = get_s3_client()
        response = s3.get_object(Bucket=settings.s3_bucket, Key=artifact.s3_key)
        content = response["Body"]

        # Determine content type
        content_type_map = {
            "diff": "text/plain",
            "test_log": "text/plain",
            "coverage": "application/xml",
            "writeup": "application/json",
            "source_bundle": "application/gzip",
            "metrics_json": "application/json",
            "llm_output": "application/json",
        }
        content_type = content_type_map.get(artifact.type.value, "application/octet-stream")

        return StreamingResponse(
            content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{artifact.s3_key.split("/")[-1]}"'
            },
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact file not found in storage",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error downloading artifact",
        )


@router.get("/{artifact_id}/metadata")
async def get_artifact_metadata(
    artifact_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get artifact metadata without downloading."""
    result = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )

    # Verify access (same as download)
    result = await db.execute(
        select(SimulationRun).where(SimulationRun.id == artifact.simulation_run_id)
    )
    run = result.scalar_one_or_none()

    result = await db.execute(select(Application).where(Application.id == run.application_id))
    application = result.scalar_one_or_none()

    result = await db.execute(select(Role).where(Role.id == application.role_id))
    role = result.scalar_one_or_none()

    result = await db.execute(
        select(Membership)
        .where(Membership.org_id == role.org_id, Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this artifact",
        )

    return {
        "id": artifact.id,
        "type": artifact.type.value,
        "sha256": artifact.sha256,
        "metadata": artifact.metadata_json,
        "created_at": artifact.created_at.isoformat(),
    }
