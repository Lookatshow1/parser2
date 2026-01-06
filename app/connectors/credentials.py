from pydantic import BaseModel, Field

from app.db.models import Platform


class StubCredentials(BaseModel):
    pass


class YandexCredentials(BaseModel):
    token: str = Field(min_length=1)
    login: str | None = None


class VkCredentials(BaseModel):
    access_token: str = Field(min_length=1)
    version: str = Field(min_length=1)
    account_id: str | None = None


class OzonCredentials(BaseModel):
    client_id: str = Field(min_length=1)
    client_secret: str = Field(min_length=1)


def get_credentials_model(platform: Platform) -> type[BaseModel]:
    if platform == Platform.yandex:
        return YandexCredentials
    if platform == Platform.vk:
        return VkCredentials
    if platform == Platform.ozon:
        return OzonCredentials
    if platform == Platform.stub:
        return StubCredentials
    raise ValueError(f"Unsupported platform: {platform}")
