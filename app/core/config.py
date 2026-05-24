from __future__ import annotations

import json
import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    APP_ENV: str = "prod"

    FRONT_ORIGIN: str = "http://localhost:4321"
    EDGE_SECRET: str = ""

    GITHUB_TOKEN: str = ""
    GITHUB_REPO_OWNER: str = ""
    GITHUB_REPO_NAME: str = ""
    GITHUB_REPO_BRANCH: str = "main"
    CONTENT_DIR: str = "content/blog"

    # Secrets Manager
    SECRETS_ARN: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


def _load_secrets(arn: str) -> dict:
    try:
        import boto3
        sm = boto3.client("secretsmanager", region_name="ap-northeast-2")
        val = sm.get_secret_value(SecretId=arn)
        return json.loads(val["SecretString"])
    except Exception as e:
        logger.error("Failed to load secrets from %s: %s", arn, e)
        return {}


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.SECRETS_ARN:
        secrets = _load_secrets(s.SECRETS_ARN)
        if secrets.get("EDGE_SECRET"):
            s.EDGE_SECRET = secrets["EDGE_SECRET"]
        if secrets.get("GITHUB_TOKEN"):
            s.GITHUB_TOKEN = secrets["GITHUB_TOKEN"]
    return s


settings = get_settings()
