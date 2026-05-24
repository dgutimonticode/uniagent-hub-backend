from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from app.services.exceptions import S3ServiceError
from app.services.s3_service import S3Service


BUCKET = "test-bucket"


@pytest.fixture
def mock_s3_client():
    return MagicMock()


@pytest.fixture
def s3(app, mock_s3_client):
    app.config["AWS_S3_BUCKET"] = BUCKET
    return S3Service(client=mock_s3_client)


def test_upload_file_calls_put_object_with_correct_params(s3, mock_s3_client):
    result = s3.upload_file(b"hello world", "agente/skill.md", "text/markdown")

    mock_s3_client.put_object.assert_called_once_with(
        Bucket=BUCKET,
        Key="agente/skill.md",
        Body=b"hello world",
        ContentType="text/markdown",
    )
    assert result == "agente/skill.md"


def test_download_file_returns_bytes(s3, mock_s3_client):
    body = MagicMock()
    body.read.return_value = b"file content"
    mock_s3_client.get_object.return_value = {"Body": body}

    result = s3.download_file("agente/skill.md")

    assert result == b"file content"
    mock_s3_client.get_object.assert_called_once_with(
        Bucket=BUCKET,
        Key="agente/skill.md",
    )


def test_delete_file_calls_delete_object(s3, mock_s3_client):
    s3.delete_file("agente/skill.md")

    mock_s3_client.delete_object.assert_called_once_with(
        Bucket=BUCKET,
        Key="agente/skill.md",
    )


def test_generate_presigned_url_returns_string(s3, mock_s3_client):
    mock_s3_client.generate_presigned_url.return_value = "https://s3.example.com/presigned"

    url = s3.generate_presigned_url("agente/skill.md", expiration=900)

    assert isinstance(url, str)
    assert url == "https://s3.example.com/presigned"
    mock_s3_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": BUCKET, "Key": "agente/skill.md"},
        ExpiresIn=900,
    )


def test_file_exists_returns_true_when_object_exists(s3, mock_s3_client):
    mock_s3_client.head_object.return_value = {"ContentLength": 42}

    assert s3.file_exists("agente/skill.md") is True
    mock_s3_client.head_object.assert_called_once_with(
        Bucket=BUCKET,
        Key="agente/skill.md",
    )


def test_file_exists_returns_false_when_object_missing(s3, mock_s3_client):
    mock_s3_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "HeadObject",
    )

    assert s3.file_exists("agente/missing.md") is False


def test_s3_service_error_raised_on_generic_client_error(s3, mock_s3_client):
    mock_s3_client.put_object.side_effect = ClientError(
        {"Error": {"Code": "InternalError", "Message": "boom"}},
        "PutObject",
    )

    with pytest.raises(S3ServiceError) as exc_info:
        s3.upload_file(b"x", "agente/skill.md", "text/markdown")

    assert exc_info.value.code == "S3_ERROR"
    assert "boom" in exc_info.value.message
