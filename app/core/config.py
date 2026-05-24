from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "prod"

    FRONT_ORIGIN: str = "http://localhost:4321"
    EDGE_SECRET: str = ""

    GITHUB_TOKEN: str = ""
    GITHUB_REPO_OWNER: str = ""
    GITHUB_REPO_NAME: str = ""
    GITHUB_REPO_BRANCH: str = "main"
    CONTENT_DIR: str = "content/blog"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
