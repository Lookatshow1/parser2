from app.connectors.ozon_performance import OzonPerformanceConnector
from app.connectors.stub import StubConnector
from app.connectors.vk_ads import VkAdsConnector
from app.connectors.yandex_direct import YandexDirectConnector
from app.db.models import Platform


class ConnectorService:
    def __init__(self) -> None:
        self._connectors = {
            Platform.yandex: YandexDirectConnector(),
            Platform.ozon: OzonPerformanceConnector(),
            Platform.vk: VkAdsConnector(),
        }

    def get(self, platform: Platform) -> StubConnector:
        return self._connectors[platform]
