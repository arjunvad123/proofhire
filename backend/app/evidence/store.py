"""Evidence artifact storage using S3/MinIO."""

import hashlib
from datetime import datetime, timedelta
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class ArtifactStore:
    """Store and retrieve evidence artifacts from S3."""

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
        )
        self.bucket = settings.S3_BUCKET

    def upload_artifact(
        self,
        run_id: str,
        artifact_type: str,
        content: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload an artifact and return the S3 key.

        Args:
            run_id: The simulation run ID
            artifact_type: Type of artifact (e.g., "diff", "testlog")
            content: File content as bytes or file-like object
            content_type: MIME type

        Returns:
            S3 key for the uploaded artifact
        """
        # Generate deterministic key
        s3_key = f"runs/{run_id}/{artifact_type}"

        try:
            if isinstance(content, bytes):
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=content,
                    ContentType=content_type,
                )
            else:
                self.s3_client.upload_fileobj(
                    content,
                    self.bucket,
                    s3_key,
                    ExtraArgs={"ContentType": content_type},
                )

            logger.info("Artifact uploaded", run_id=run_id, type=artifact_type, key=s3_key)
            return s3_key

        except ClientError as e:
            logger.error("Failed to upload artifact", error=str(e))
            raise

    def get_artifact(self, s3_key: str) -> bytes:
        """Download an artifact by S3 key."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            return response["Body"].read()
        except ClientError as e:
            logger.error("Failed to get artifact", key=s3_key, error=str(e))
            raise

    def get_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for artifact download.

        Args:
            s3_key: S3 key of the artifact
            expires_in: URL expiration in seconds (default 1 hour)

        Returns:
            Presigned URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error("Failed to generate presigned URL", key=s3_key, error=str(e))
            raise

    def artifact_exists(self, s3_key: str) -> bool:
        """Check if an artifact exists."""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError:
            return False

    def delete_artifact(self, s3_key: str) -> None:
        """Delete an artifact."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info("Artifact deleted", key=s3_key)
        except ClientError as e:
            logger.error("Failed to delete artifact", key=s3_key, error=str(e))
            raise

    def compute_hash(self, content: bytes) -> str:
        """Compute SHA-256 hash of content for integrity verification."""
        return hashlib.sha256(content).hexdigest()


# Global instance
_store: ArtifactStore | None = None


def get_artifact_store() -> ArtifactStore:
    """Get the global artifact store instance."""
    global _store
    if _store is None:
        _store = ArtifactStore()
    return _store
