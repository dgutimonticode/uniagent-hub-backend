import os
from datetime import timedelta


class MissingEnvError(RuntimeError):
    def __init__(self, names: list[str]) -> None:
        super().__init__(
            f"Faltan variables de entorno requeridas en producción: {', '.join(names)}"
        )
        self.names = names


def _parse_cors(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class BaseConfig:
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24"))
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    SQS_SKILLS_QUEUE_URL = os.getenv("SQS_SKILLS_QUEUE_URL", "")

    AGENT_API_URL = os.getenv("AGENT_API_URL", "")
    AGENT_HMAC_SECRET = os.getenv("AGENT_HMAC_SECRET", "")
    CF_ACCESS_CLIENT_ID = os.getenv("CF_ACCESS_CLIENT_ID", "")
    CF_ACCESS_CLIENT_SECRET = os.getenv("CF_ACCESS_CLIENT_SECRET", "")


class DevConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = True

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-change-in-prod")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "mysql+pymysql://root:password@db:3306/uniagent"
    )

    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "http://localstack:4566")
    CORS_ORIGINS = _parse_cors(os.getenv("CORS_ORIGINS", "http://localhost:5173"))


class TestConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = "test-secret-32-bytes-long-for-hs256-ok"
    JWT_SECRET_KEY = "test-jwt-secret-32-bytes-long-for-hs256-x"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
    CORS_ORIGINS = ["http://localhost:5173"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProdConfig(BaseConfig):
    """Producción: secretos y DB son obligatorios. Sin defaults. Fail-fast al instanciar."""

    DEBUG = False
    SQLALCHEMY_ECHO = False
    AWS_S3_ENDPOINT_URL = None  # boto3 usa el endpoint real de AWS

    REQUIRED_VARS = ("SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL", "CORS_ORIGINS")

    def __init__(self) -> None:
        missing = [name for name in self.REQUIRED_VARS if not os.getenv(name)]
        if missing:
            raise MissingEnvError(missing)

        self.SECRET_KEY = os.environ["SECRET_KEY"]
        self.JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
        self.SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
        self.CORS_ORIGINS = _parse_cors(os.environ["CORS_ORIGINS"])


class _ConfigRegistry:
    _eager: dict[str, type] = {
        "development": DevConfig,
        "testing": TestConfig,
        "default": DevConfig,
    }

    def __getitem__(self, key: str):
        if key == "production":
            return ProdConfig()
        return self._eager[key]


config = _ConfigRegistry()
