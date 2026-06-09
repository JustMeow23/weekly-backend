import asyncio
import uuid
from functools import partial

import boto3
from botocore.exceptions import ClientError

from app.config import settings

_s3_client = None


def _get_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
        )
    return _s3_client


def _upload_fileobj_sync(file_bytes: bytes, key: str, content_type: str) -> str:
    import io
    client = _get_client()
    client.upload_fileobj(
        io.BytesIO(file_bytes),
        settings.S3_BUCKET,
        key,
        ExtraArgs={"ContentType": content_type, "ACL": "public-read"},
    )
    return f"{settings.S3_PUBLIC_URL}/{key}"


async def upload_avatar(file_bytes: bytes, content_type: str) -> str:
    ext = content_type.split("/")[-1]
    key = f"avatars/{uuid.uuid4()}.{ext}"
    loop = asyncio.get_event_loop()
    url = await loop.run_in_executor(
        None, partial(_upload_fileobj_sync, file_bytes, key, content_type)
    )
    return url
