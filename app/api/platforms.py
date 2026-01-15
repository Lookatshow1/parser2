from fastapi import APIRouter

from app.db.models import Platform


router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("")
def list_platforms():
    return {
        "платформы": [
            {
                "код": Platform.yandex.value,
                "название": "Яндекс.Директ",
                "возможности": {
                    "синк": "mock",
                    "импорт": "mock",
                    "черновики": True,
                    "публикация": False,
                },
            },
            {
                "код": Platform.vk.value,
                "название": "VK Ads",
                "возможности": {
                    "синк": "нет",
                    "импорт": "нет",
                    "черновики": True,
                    "публикация": False,
                },
            },
            {
                "код": Platform.ozon.value,
                "название": "Ozon Performance",
                "возможности": {
                    "синк": "нет",
                    "импорт": "нет",
                    "черновики": True,
                    "публикация": False,
                },
            },
        ]
    }
