from pydantic_settings import BaseSettings
from pydantic import computed_field

class Settings(BaseSettings):
    port: int = 6767
    host: str = "0.0.0.0"
    
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    RANDOM_SECRET: str = "secret"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    S3_ENDPOINT_URL: str = "https://s3.komaru-best.cfd"
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str = "weekly"
    S3_PUBLIC_URL: str = "https://s3.komaru-best.cfd/weekly"
    DEFAULT_AVATAR_URL: str = "https://s3.komaru-best.cfd/weekly/avatars/default.png"

    FIREBASE_CREDENTIALS_PATH: str = ""

    YANDEX_CAPTCHA_SECRET_KEY: str = ""

    CAPTCHA_ENABLED: bool = True
    EMAIL_CODE_ENABLED: bool = False

    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "noreply@weekly.komaru-best.cfd"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = "https://gate.trinity.tg/aurora"

    ANDROID_PACKAGE_NAME: str = "com.livesgood.weekly_app"
    ANDROID_SHA256_FINGERPRINTS: str = "DF:A7:D8:23:2F:F5:F8:3E:3D:5C:E9:96:D9:ED:68:D7:00:0F:D0:F4:0F:CE:9A:CC:2C:05:6A:48:A9:D3:27:12"
    APP_SCHEME: str = "weekly"
    APP_DOWNLOAD_URL: str = "https://t.me/weekly_app"

    @computed_field
    @property
    def android_fingerprints_list(self) -> list[str]:
        return [f.strip() for f in self.ANDROID_SHA256_FINGERPRINTS.split(",") if f.strip()]

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
    
settings = Settings()