from typing import Dict, Any
from app.db.models import Platform
from app.connectors.base import AdsConnector
from app.connectors.yandex_direct import YandexDirectConnector
from app.connectors.ozon_performance import OzonPerformanceConnector
from app.connectors.vk_ads import VkAdsConnector
from app.connectors.stub import StubConnector
from app.security.credentials_crypto import maybe_decrypt

def get_connector(platform: Platform, credentials: Dict[str, Any]) -> AdsConnector:
    decrypted = maybe_decrypt(credentials)
    if platform == Platform.yandex:
        return YandexDirectConnector(decrypted)
    elif platform == Platform.ozon:
        return OzonPerformanceConnector(decrypted)
    elif platform == Platform.vk:
        return VkAdsConnector(decrypted)
    elif platform == Platform.stub:
        return StubConnector(decrypted)
    else:
        raise ValueError(f"Unsupported platform: {platform}")
