import boto3
from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)
from flask import current_app

from app.services.exceptions import S3ServiceError


# TODO: implement `flask init-s3` CLI command to create the bucket in LocalStack.
# Referenced in docs/05_backend_guide.md (Quickstart) but not implemented yet.
# Deferred from ASL-13; pair with ASL-14 or a small dedicated issue.


_TIMEOUT_ERRORS = (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError)


class S3Service:
    def __init__(self, *, client=None) -> None:
        self._client = client

    @property
    def client(self):
        if self._client is None:
            self._client = self._build_client()
        return self._client

    @property
    def bucket(self) -> str:
        return current_app.config["AWS_S3_BUCKET"]

    def _build_client(self):
        config = current_app.config
        kwargs = {
            "region_name": config["AWS_REGION"],
            "aws_access_key_id": config.get("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": config.get("AWS_SECRET_ACCESS_KEY"),
        }
        endpoint = config.get("AWS_S3_ENDPOINT_URL")
        if endpoint:
            kwargs["endpoint_url"] = endpoint
        return boto3.client("s3", **kwargs)

    def upload_file(self, file_obj, s3_key: str, content_type: str) -> str:
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=file_obj,
                ContentType=content_type,
            )
            return s3_key
        except ClientError as e:
            raise self._wrap_error(e, "upload_file") from e
        except _TIMEOUT_ERRORS as e:
            raise S3ServiceError("S3_TIMEOUT", f"Timeout uploading to S3: {e}") from e

    def download_file(self, s3_key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=s3_key)
            return response["Body"].read()
        except ClientError as e:
            raise self._wrap_error(e, "download_file") from e
        except _TIMEOUT_ERRORS as e:
            raise S3ServiceError("S3_TIMEOUT", f"Timeout downloading from S3: {e}") from e

    def delete_file(self, s3_key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
        except ClientError as e:
            raise self._wrap_error(e, "delete_file") from e
        except _TIMEOUT_ERRORS as e:
            raise S3ServiceError("S3_TIMEOUT", f"Timeout deleting from S3: {e}") from e

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=expiration,
            )
        except ClientError as e:
            raise self._wrap_error(e, "generate_presigned_url") from e

    def file_exists(self, s3_key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("404", "NoSuchKey", "NotFound"):
                return False
            raise self._wrap_error(e, "file_exists") from e
        except _TIMEOUT_ERRORS as e:
            raise S3ServiceError("S3_TIMEOUT", f"Timeout checking S3 object: {e}") from e

    @staticmethod
    def _wrap_error(error: ClientError, operation: str) -> S3ServiceError:
        info = error.response.get("Error", {})
        code = info.get("Code", "Unknown")
        message = info.get("Message", str(error))

        if code in ("NoSuchKey", "404", "NotFound"):
            return S3ServiceError("S3_NOT_FOUND", f"S3 object not found: {message}")
        if code == "NoSuchBucket":
            return S3ServiceError("S3_NO_SUCH_BUCKET", f"S3 bucket does not exist: {message}")
        if code in ("AccessDenied", "403"):
            return S3ServiceError("S3_ACCESS_DENIED", f"Access denied to S3: {message}")
        return S3ServiceError("S3_ERROR", f"S3 error in {operation}: {message}")


s3_service = S3Service()
