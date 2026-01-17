"""
Demo Account Seeder.

Creates lookatshow@yandex.ru with realistic demo data.
Run: python -m scripts.seed_demo_account
"""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import User, Organization, Membership, MembershipRole
from app.db.models_billing import BillingAccount, BillingTransaction, TransactionType, TransactionStatus
from app.db.models_drafts import DraftCampaign, DraftAdGroup, DraftAd
from app.db import models_magic  # Import to resolve relationships
import bcrypt

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Demo account credentials
DEMO_EMAIL = "lookatshow@yandex.ru"
DEMO_PASSWORD = "19910923Cfif"
DEMO_ORG_NAME = "Look At Show Agency"


def create_demo_user(db: Session) -> tuple:
    """Create or get demo user and organization."""
    
    # Check if user exists
    existing = db.query(User).filter(User.email == DEMO_EMAIL).first()
    if existing:
        print(f"User {DEMO_EMAIL} already exists (id={existing.id})")
        org = db.query(Organization).filter(
            Organization.id == existing.active_organization_id
        ).first()
        return existing, org
    
    # Create organization
    org = Organization(
        name=DEMO_ORG_NAME,
        created_at=datetime.utcnow() - timedelta(days=90),
    )
    db.add(org)
    db.flush()
    
    # Create user
    user = User(
        email=DEMO_EMAIL,
        password_hash=get_password_hash(DEMO_PASSWORD),
        is_active=True,
        active_organization_id=org.id,
        created_at=datetime.utcnow() - timedelta(days=90),
    )
    db.add(user)
    db.flush()
    
    # Create membership
    membership = Membership(
        user_id=user.id,
        organization_id=org.id,
        role=MembershipRole.owner.value,
    )
    db.add(membership)
    
    print(f"Created user {DEMO_EMAIL} (id={user.id}) in org {org.name} (id={org.id})")
    return user, org


def create_demo_campaigns(db: Session, org: Organization):
    """Create realistic demo campaigns."""
    
    campaigns_data = [
        {
            "name": "Яндекс — Бренд Look At Show",
            "platform": "yandex",
            "status": "active",
            "ads": [
                {"title": "Look At Show — Мероприятия", "text": "Корпоративы, презентации, юбилеи. 12 лет опыта. Скидка 15%!"},
                {"title": "Мероприятия под ключ", "text": "От идеи до реализации за 7 дней. Команда профессионалов."},
                {"title": "Event-агентство #1", "text": "500+ успешных проектов. Работаем по всей России."},
            ],
        },
        {
            "name": "VK — Таргет на предпринимателей",
            "platform": "vk",
            "status": "active",
            "ads": [
                {"title": "Корпоратив мечты", "text": "Организуем незабываемый корпоратив для вашей команды."},
                {"title": "Презентация продукта", "text": "Эффектная презентация — залог успешных продаж."},
            ],
        },
        {
            "name": "Ozon — Аренда оборудования",
            "platform": "ozon",
            "status": "draft",
            "ads": [
                {"title": "Звуковое оборудование", "text": "Профессиональный звук для мероприятий любого масштаба."},
            ],
        },
        {
            "name": "Яндекс — Свадьбы премиум",
            "platform": "yandex",
            "status": "active",
            "ads": [
                {"title": "Свадьба вашей мечты", "text": "Полная организация свадьбы. От 500 000₽. Без скрытых платежей."},
                {"title": "Свадебное агентство", "text": "Идеальная свадьба без стресса. Персональный менеджер 24/7."},
                {"title": "Свадьба в Москве и МО", "text": "Лучшие площадки, декор, кейтеринг. Скидка на зимние даты!"},
                {"title": "VIP-свадьбы", "text": "Эксклюзивные мероприятия для требовательных клиентов."},
            ],
        },
        {
            "name": "VK — Ретаргетинг сайт",
            "platform": "vk",
            "status": "paused",
            "ads": [
                {"title": "Вернитесь к нам!", "text": "Специальное предложение — скидка 10% на первый заказ."},
            ],
        },
    ]
    
    for camp_data in campaigns_data:
        # Check if campaign exists
        existing = db.query(DraftCampaign).filter(
            DraftCampaign.organization_id == org.id,
            DraftCampaign.name == camp_data["name"],
        ).first()
        
        if existing:
            print(f"  Campaign '{camp_data['name']}' already exists")
            continue
        
        # Create campaign
        campaign = DraftCampaign(
            organization_id=org.id,
            name=camp_data["name"],
            platform=camp_data["platform"],
            status=camp_data["status"],
            payload_json={
                "budget": random.randint(5000, 50000),
                "landing_url": "https://lookatshow.ru",
            },
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
        )
        db.add(campaign)
        db.flush()
        
        # Create ad group
        ad_group = DraftAdGroup(
            campaign_id=campaign.id,
            name="Основная группа",
        )
        db.add(ad_group)
        db.flush()
        
        # Create ads
        for ad_data in camp_data["ads"]:
            ad = DraftAd(
                ad_group_id=ad_group.id,
                title=ad_data["title"],
                text=ad_data["text"],
                landing_url="https://lookatshow.ru",
            )
            db.add(ad)
        
        print(f"  Created campaign '{camp_data['name']}' with {len(camp_data['ads'])} ads")
    
    db.flush()


def create_demo_billing(db: Session, org: Organization):
    """Create realistic billing data."""
    
    # Check if account exists
    existing_account = db.query(BillingAccount).filter(
        BillingAccount.organization_id == org.id
    ).first()
    
    if existing_account:
        print(f"  Billing account already exists with balance {existing_account.balance}")
        return
    
    # Create billing account
    account = BillingAccount(
        organization_id=org.id,
        balance=Decimal("47500.00"),
        currency="RUB",
    )
    db.add(account)
    db.flush()
    
    # Create transactions
    transactions = [
        {"amount": 100000, "type": TransactionType.topup, "days_ago": 45},
        {"amount": -15000, "type": TransactionType.spend, "days_ago": 40},
        {"amount": -12000, "type": TransactionType.spend, "days_ago": 35},
        {"amount": 50000, "type": TransactionType.topup, "days_ago": 30},
        {"amount": -18500, "type": TransactionType.spend, "days_ago": 25},
        {"amount": -8000, "type": TransactionType.spend, "days_ago": 20},
        {"amount": -25000, "type": TransactionType.spend, "days_ago": 15},
        {"amount": 30000, "type": TransactionType.topup, "days_ago": 10},
        {"amount": -9000, "type": TransactionType.spend, "days_ago": 5},
        {"amount": -5000, "type": TransactionType.spend, "days_ago": 3},
        {"amount": -15000, "type": TransactionType.spend, "days_ago": 1},
        {"amount": -25000, "type": TransactionType.spend, "days_ago": 0},
    ]
    
    for tx in transactions:
        transaction = BillingTransaction(
            organization_id=org.id,
            amount=Decimal(str(abs(tx["amount"]))),
            type=tx["type"],
            status=TransactionStatus.succeeded,
            created_at=datetime.utcnow() - timedelta(days=tx["days_ago"]),
        )
        db.add(transaction)
    
    print(f"  Created billing account with balance ₽47,500 and {len(transactions)} transactions")


def main():
    """Main seeder function."""
    print("=" * 60)
    print("🌱 Seeding Demo Account")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Create user and org
        user, org = create_demo_user(db)
        
        print("\n📦 Creating campaigns...")
        create_demo_campaigns(db, org)
        
        print("\n💰 Creating billing data...")
        create_demo_billing(db, org)
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ Demo account ready!")
        print(f"   Email: {DEMO_EMAIL}")
        print(f"   Password: {DEMO_PASSWORD}")
        print(f"   Organization: {DEMO_ORG_NAME}")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
