import boto3

from app.core.config import settings

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
)


def upload_bytes(key: str, data: bytes, content_type: str) -> None:
    _s3.put_object(
        Bucket=settings.s3_bucket_name,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


def get_bytes(key: str) -> bytes:
    response = _s3.get_object(Bucket=settings.s3_bucket_name, Key=key)
    return response["Body"].read()


def delete_object(key: str) -> None:
    # DELETE do S3/MinIO já é idempotente por natureza — apagar uma key que
    # não existe não levanta erro, então não precisa de try/except aqui.
    _s3.delete_object(Bucket=settings.s3_bucket_name, Key=key)