"""
Mock AI Providers for development and testing.
"""
import random
import asyncio
from typing import Any, Optional
from .interfaces import TextProvider, ImageProvider, WebScanner


class MockTextProvider(TextProvider):
    """Mock text provider that returns realistic ad content."""
    
    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: str = None,
        temperature: float = 0.7, 
        json_schema: dict = None
    ) -> str | dict:
        """Generate mock ad content with realistic Russian ads."""
        await asyncio.sleep(1.0)  # Simulate API delay
        
        if json_schema:
            # Return realistic ad content
            return {
                "business_name": "Ваш бизнес",
                "business_type": "услуги",
                "ads": [
                    {"title": "Скидка 30% до конца недели!", "text": "Успейте заказать со скидкой. Доставка бесплатно по всей России!", "approach": "скидка"},
                    {"title": "Только 3 места осталось", "text": "Спешите записаться! Акция ограничена. Звоните сейчас!", "approach": "срочность"},
                    {"title": "№1 в своей нише", "text": "Лидер рынка с 2015 года. Гарантия качества и надёжности!", "approach": "уникальность"},
                    {"title": "10 000+ довольных клиентов", "text": "Присоединяйтесь к лучшим! Рейтинг 5.0 на Яндексе", "approach": "доверие"},
                    {"title": "Экономьте до 50%", "text": "Лучшие цены на рынке. Убедитесь сами — сравните!", "approach": "выгода"},
                    {"title": "Бесплатная консультация", "text": "Эксперт ответит на все вопросы за 5 минут. Оставьте заявку!", "approach": "выгода"},
                    {"title": "Акция заканчивается!", "text": "Специальное предложение только для новых клиентов!", "approach": "срочность"},
                    {"title": "Качество проверено временем", "text": "Работаем для вас уже 10 лет. Тысячи отзывов!", "approach": "доверие"},
                    {"title": "Эксклюзивные условия", "text": "Только у нас такие цены и сервис. Проверьте!", "approach": "уникальность"},
                    {"title": "Подарок при заказе", "text": "Закажите сегодня и получите бонус до 5000₽!", "approach": "скидка"},
                ]
            }
        
        return "This is a mock AI response."


class MockImageProvider(ImageProvider):
    """Mock image provider that returns placeholder images."""
    
    async def generate_image(self, prompt: str, size: str = "1024x1024") -> str:
        """Generate a single image URL."""
        await asyncio.sleep(0.5)
        
        # Use picsum for realistic placeholder images
        seed = random.randint(1, 1000)
        return f"https://picsum.photos/seed/{seed}/400/400"
    
    async def generate_images(self, prompt: str, n: int = 1, size: str = "1024x1024") -> list[str]:
        """Generate multiple image URLs."""
        await asyncio.sleep(0.5)
        
        images = []
        for i in range(n):
            seed = random.randint(1, 1000)
            images.append(f"https://picsum.photos/seed/{seed}/400/400")
        
        return images


class MockWebScanner(WebScanner):
    """Mock web scanner for testing."""
    
    async def fetch_site_profile(self, domain: str) -> dict:
        await asyncio.sleep(0.5)
        return {
            "title": f"Mock Title for {domain}",
            "description": "Mock description of the website.",
            "summary": "This website sells things."
        }
