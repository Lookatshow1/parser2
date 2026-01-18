"""
Industry Templates and Benchmarks.

Pre-built campaign templates and CTR/CPA benchmarks by industry.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# INDUSTRIES
# =============================================================================

class Industry(str, Enum):
    """Supported industries for templates."""
    ECOMMERCE = "ecommerce"               # Интернет-магазины
    SERVICES = "services"                  # Услуги
    EDUCATION = "education"                # Образование, курсы
    REALESTATE = "realestate"             # Недвижимость
    AUTO = "auto"                          # Автомобили, услуги
    MEDICINE = "medicine"                  # Медицина, клиники
    BEAUTY = "beauty"                      # Красота, салоны
    RESTAURANTS = "restaurants"            # Рестораны, доставка еды
    LEGAL = "legal"                        # Юридические услуги
    FINANCE = "finance"                    # Финансы, кредиты
    TRAVEL = "travel"                      # Туризм, путешествия
    EVENTS = "events"                      # Мероприятия, event


# =============================================================================
# BENCHMARKS
# =============================================================================

@dataclass
class IndustryBenchmark:
    """Industry-specific benchmark metrics."""
    industry: Industry
    avg_ctr: float        # средний CTR в %
    avg_cpc: float        # средний CPC в рублях
    avg_cpa: float        # средний CPA в рублях
    avg_roas: float       # средний ROAS
    conversion_rate: float  # средний CR в %


BENCHMARKS: Dict[Industry, IndustryBenchmark] = {
    Industry.ECOMMERCE: IndustryBenchmark(
        industry=Industry.ECOMMERCE,
        avg_ctr=2.5,
        avg_cpc=25,
        avg_cpa=800,
        avg_roas=4.5,
        conversion_rate=2.8,
    ),
    Industry.SERVICES: IndustryBenchmark(
        industry=Industry.SERVICES,
        avg_ctr=3.2,
        avg_cpc=40,
        avg_cpa=1500,
        avg_roas=3.0,
        conversion_rate=4.5,
    ),
    Industry.EDUCATION: IndustryBenchmark(
        industry=Industry.EDUCATION,
        avg_ctr=2.8,
        avg_cpc=35,
        avg_cpa=2000,
        avg_roas=5.0,
        conversion_rate=3.0,
    ),
    Industry.REALESTATE: IndustryBenchmark(
        industry=Industry.REALESTATE,
        avg_ctr=1.5,
        avg_cpc=120,
        avg_cpa=8000,
        avg_roas=10.0,
        conversion_rate=1.2,
    ),
    Industry.AUTO: IndustryBenchmark(
        industry=Industry.AUTO,
        avg_ctr=2.0,
        avg_cpc=45,
        avg_cpa=3500,
        avg_roas=6.0,
        conversion_rate=2.0,
    ),
    Industry.MEDICINE: IndustryBenchmark(
        industry=Industry.MEDICINE,
        avg_ctr=2.2,
        avg_cpc=80,
        avg_cpa=2500,
        avg_roas=4.0,
        conversion_rate=3.5,
    ),
    Industry.BEAUTY: IndustryBenchmark(
        industry=Industry.BEAUTY,
        avg_ctr=3.5,
        avg_cpc=30,
        avg_cpa=1200,
        avg_roas=3.5,
        conversion_rate=5.0,
    ),
    Industry.RESTAURANTS: IndustryBenchmark(
        industry=Industry.RESTAURANTS,
        avg_ctr=4.0,
        avg_cpc=20,
        avg_cpa=600,
        avg_roas=5.0,
        conversion_rate=6.0,
    ),
    Industry.LEGAL: IndustryBenchmark(
        industry=Industry.LEGAL,
        avg_ctr=1.8,
        avg_cpc=150,
        avg_cpa=5000,
        avg_roas=8.0,
        conversion_rate=2.0,
    ),
    Industry.FINANCE: IndustryBenchmark(
        industry=Industry.FINANCE,
        avg_ctr=1.5,
        avg_cpc=200,
        avg_cpa=4000,
        avg_roas=6.0,
        conversion_rate=1.5,
    ),
    Industry.TRAVEL: IndustryBenchmark(
        industry=Industry.TRAVEL,
        avg_ctr=3.0,
        avg_cpc=35,
        avg_cpa=2000,
        avg_roas=4.0,
        conversion_rate=3.0,
    ),
    Industry.EVENTS: IndustryBenchmark(
        industry=Industry.EVENTS,
        avg_ctr=2.8,
        avg_cpc=50,
        avg_cpa=3000,
        avg_roas=5.0,
        conversion_rate=2.5,
    ),
}


# =============================================================================
# CAMPAIGN TEMPLATES
# =============================================================================

@dataclass
class AdTemplate:
    """Template for an ad."""
    title: str
    text: str
    approach: str  # emotional, rational, usp


@dataclass
class CampaignTemplate:
    """Pre-built campaign template for an industry."""
    industry: Industry
    name: str
    description: str
    recommended_budget: int  # рублей в день
    recommended_bid: int     # рублей за клик
    keywords: List[str]
    negative_keywords: List[str]
    ads: List[AdTemplate]
    tips: List[str]


TEMPLATES: Dict[Industry, List[CampaignTemplate]] = {
    Industry.ECOMMERCE: [
        CampaignTemplate(
            industry=Industry.ECOMMERCE,
            name="Брендовый трафик",
            description="Реклама по названию магазина и бренда",
            recommended_budget=2000,
            recommended_bid=15,
            keywords=["[название_магазина]", "купить [товар]", "заказать [товар]"],
            negative_keywords=["бесплатно", "скачать", "отзывы"],
            ads=[
                AdTemplate("Скидка 30% сегодня", "Официальный магазин. Доставка 1-2 дня. Заходите!", "emotional"),
                AdTemplate("Бесплатная доставка", "При заказе от 3000₽. Гарантия качества 100%", "rational"),
                AdTemplate("Только у нас", "Эксклюзивные товары по лучшим ценам. Закажите!", "usp"),
            ],
            tips=["Используйте динамические подстановки", "Добавьте быстрые ссылки"],
        ),
        CampaignTemplate(
            industry=Industry.ECOMMERCE,
            name="Ретаргетинг",
            description="Возврат посетителей, которые не купили",
            recommended_budget=1500,
            recommended_bid=20,
            keywords=["ретаргетинг"],
            negative_keywords=[],
            ads=[
                AdTemplate("Вы забыли корзину!", "Товары ждут вас. Скидка 10% на первый заказ", "emotional"),
                AdTemplate("Вернитесь за покупками", "Бесплатная доставка для вас сегодня", "rational"),
            ],
            tips=["Сегментируйте по категориям товаров", "Ограничьте частоту показа"],
        ),
    ],
    Industry.SERVICES: [
        CampaignTemplate(
            industry=Industry.SERVICES,
            name="Локальные услуги",
            description="Привлечение клиентов в своём городе",
            recommended_budget=1500,
            recommended_bid=30,
            keywords=["[услуга] [город]", "[услуга] рядом", "[услуга] недорого"],
            negative_keywords=["вакансии", "работа", "курсы"],
            ads=[
                AdTemplate("Мастер за 1 час", "Быстро, качественно, недорого. Гарантия на работы!", "emotional"),
                AdTemplate("Рейтинг 4.9★", "1000+ довольных клиентов. Звоните прямо сейчас!", "rational"),
                AdTemplate("Скидка 20% новым", "Первый заказ со скидкой. Профессионалы своего дела", "usp"),
            ],
            tips=["Добавьте номер телефона", "Укажите время работы"],
        ),
    ],
    Industry.BEAUTY: [
        CampaignTemplate(
            industry=Industry.BEAUTY,
            name="Салон красоты",
            description="Привлечение клиентов в салон",
            recommended_budget=1000,
            recommended_bid=25,
            keywords=["маникюр [город]", "стрижка рядом", "салон красоты"],
            negative_keywords=["обучение", "курсы"],
            ads=[
                AdTemplate("Маникюр 1500₽", "Запись онлайн за 30 сек. Уютный салон в центре", "emotional"),
                AdTemplate("Мастера со стажем 5+ лет", "Только качественные материалы. Записывайтесь!", "rational"),
                AdTemplate("Первый визит -30%", "Попробуйте нас с выгодой. Ждём вас!", "usp"),
            ],
            tips=["Добавьте фото работ", "Используйте расширения с акциями"],
        ),
    ],
    Industry.RESTAURANTS: [
        CampaignTemplate(
            industry=Industry.RESTAURANTS,
            name="Доставка еды",
            description="Привлечение заказов на доставку",
            recommended_budget=2000,
            recommended_bid=15,
            keywords=["доставка еды [город]", "пицца доставка", "суши заказать"],
            negative_keywords=["рецепты", "готовить"],
            ads=[
                AdTemplate("Доставка за 30 минут", "Горячая еда прямо к вам. Закажите сейчас!", "emotional"),
                AdTemplate("Скидка 15% на первый заказ", "Вкусно, быстро, недорого. Промокод НОВЫЙ", "rational"),
                AdTemplate("2000+ отзывов 5★", "Любимый ресторан города теперь доставляет!", "usp"),
            ],
            tips=["Используйте акции в быстрых ссылках", "Добавьте меню в расширения"],
        ),
    ],
    Industry.EVENTS: [
        CampaignTemplate(
            industry=Industry.EVENTS,
            name="Event-агентство",
            description="Привлечение корпоративных клиентов",
            recommended_budget=3000,
            recommended_bid=50,
            keywords=["организация мероприятий", "корпоратив под ключ", "event-агентство"],
            negative_keywords=["вакансии", "работа"],
            ads=[
                AdTemplate("Корпоратив мечты", "12 лет опыта. 500+ проектов. Звоните!", "emotional"),
                AdTemplate("Мероприятие за 14 дней", "От идеи до реализации. Персональный менеджер", "rational"),
                AdTemplate("Агентство года 2025", "Победитель премии Event Awards. Только лучшее!", "usp"),
            ],
            tips=["Используйте кейсы в объявлениях", "Добавьте ссылку на портфолио"],
        ),
    ],
}


# =============================================================================
# API
# =============================================================================

def get_benchmark(industry: Industry) -> Optional[IndustryBenchmark]:
    """Get benchmark metrics for an industry."""
    return BENCHMARKS.get(industry)


def get_templates(industry: Industry) -> List[CampaignTemplate]:
    """Get campaign templates for an industry."""
    return TEMPLATES.get(industry, [])


def get_all_industries() -> List[Dict[str, str]]:
    """Get list of all supported industries with Russian names."""
    names = {
        Industry.ECOMMERCE: "Интернет-магазины",
        Industry.SERVICES: "Услуги",
        Industry.EDUCATION: "Образование",
        Industry.REALESTATE: "Недвижимость",
        Industry.AUTO: "Автомобили",
        Industry.MEDICINE: "Медицина",
        Industry.BEAUTY: "Красота",
        Industry.RESTAURANTS: "Рестораны",
        Industry.LEGAL: "Юридические услуги",
        Industry.FINANCE: "Финансы",
        Industry.TRAVEL: "Туризм",
        Industry.EVENTS: "Мероприятия",
    }
    return [{"id": ind.value, "name": names[ind]} for ind in Industry]


def compare_with_benchmark(
    industry: Industry,
    actual_ctr: float,
    actual_cpc: float,
    actual_cpa: Optional[float] = None,
) -> Dict[str, Any]:
    """Compare actual metrics with industry benchmark."""
    benchmark = get_benchmark(industry)
    if not benchmark:
        return {"error": "Unknown industry"}
    
    return {
        "industry": industry.value,
        "ctr": {
            "actual": actual_ctr,
            "benchmark": benchmark.avg_ctr,
            "diff_percent": round((actual_ctr - benchmark.avg_ctr) / benchmark.avg_ctr * 100, 1),
            "status": "good" if actual_ctr >= benchmark.avg_ctr else "below",
        },
        "cpc": {
            "actual": actual_cpc,
            "benchmark": benchmark.avg_cpc,
            "diff_percent": round((actual_cpc - benchmark.avg_cpc) / benchmark.avg_cpc * 100, 1),
            "status": "good" if actual_cpc <= benchmark.avg_cpc else "high",
        },
        "cpa": {
            "actual": actual_cpa,
            "benchmark": benchmark.avg_cpa,
            "diff_percent": round((actual_cpa - benchmark.avg_cpa) / benchmark.avg_cpa * 100, 1) if actual_cpa else None,
            "status": "good" if actual_cpa and actual_cpa <= benchmark.avg_cpa else "high" if actual_cpa else None,
        } if actual_cpa else None,
    }
