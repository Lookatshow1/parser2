from typing import Dict, Any
from app.db.models import Platform
from app.connectors.base import AdsConnector
from app.connectors.yandex_direct import YandexDirectConnector
from app.connectors.ozon_performance import OzonPerformanceConnector
from app.connectors.vk_ads import VkAdsConnector
from app.connectors.stub import StubConnector

def get_connector(platform: Platform, credentials: Dict[str, Any]) -> AdsConnector:
    if platform == Platform.yandex:
        return YandexDirectConnector(credentials)
    elif platform == Platform.ozon:
        return OzonPerformanceConnector(credentials)
    elif platform == Platform.vk:
        return VkAdsConnector(credentials)
    elif platform == Platform.stub:
        return StubConnector(credentials)
    else:
        raise ValueError(f"Unsupported platform: {platform}")
