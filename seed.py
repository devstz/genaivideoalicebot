"""
Seed script — fills the database with initial templates, packs, and an AI model.
Run: python seed.py
"""
import asyncio
import sys

from db.session import SessionFactory
from db.models import AiModel, Template, Pack
from enums import TemplateStatus


TEMPLATES = [
    {
        "name": "😊 Лёгкая мимика",
        "category": "face",
        "base_prompt": "Animate the face with a gentle smile, soft blink, and a playful wink. "
                       "Keep the expression warm and natural. {additional_text}",
        "negative_prompt": "blurry, distorted face, unnatural movements, creepy",
        "status": TemplateStatus.ACTIVE,
    },
    {
        "name": "💕 Романтика",
        "category": "face",
        "base_prompt": "Create a romantic portrait animation: the person slowly looks into the camera "
                       "with a gentle loving gaze, hair slightly moves in the breeze, "
                       "a soft smile appears. {additional_text}",
        "negative_prompt": "blurry, distorted, ugly, deformed, glitch",
        "status": TemplateStatus.ACTIVE,
    },
    {
        "name": "🎭 Эмоции",
        "category": "face",
        "base_prompt": "Animate vivid emotions on the face: joyful laughter transitioning to surprise, "
                       "then a gentle tear of happiness. Expressive and cinematic. {additional_text}",
        "negative_prompt": "blurry, distorted, unnatural expressions, creepy smile",
        "status": TemplateStatus.ACTIVE,
    },
    {
        "name": "🔄 Поворот головы",
        "category": "motion",
        "base_prompt": "Animate a smooth, cinematic head turn from front-facing to a 3/4 profile view. "
                       "Natural and elegant movement. {additional_text}",
        "negative_prompt": "blurry, distorted, jerky motion, unnatural neck",
        "status": TemplateStatus.ACTIVE,
    },
    {
        "name": "🐾 Животные",
        "category": "animals",
        "base_prompt": "Bring the animal to life: gentle tail wagging, curious head tilt, "
                       "blinking eyes, natural breathing movement. Cute and lifelike. {additional_text}",
        "negative_prompt": "blurry, distorted anatomy, unnatural movement, creepy",
        "status": TemplateStatus.ACTIVE,
    },
    {
        "name": "💃 Танец",
        "category": "motion",
        "base_prompt": "Animate the person with smooth dancing movements: gentle body sway, "
                       "rhythmic head bops, natural arm flow. Energetic and fun. {additional_text}",
        "negative_prompt": "blurry, broken limbs, unnatural pose, distorted body",
        "status": TemplateStatus.ACTIVE,
    },
    {
        "name": "🎬 Сюжетный клип",
        "category": "scene",
        "base_prompt": "Create a short cinematic scene: the person performs a natural action — "
                       "puts on sunglasses, blows out a candle, waves at the camera, or picks up a cup. "
                       "Smooth and realistic. {additional_text}",
        "negative_prompt": "blurry, distorted hands, unnatural objects, glitch artifacts",
        "status": TemplateStatus.ACTIVE,
    },
]

PACKS = [
    {
        "name": "🎬 Стартовый",
        "description": "Идеально для первого знакомства",
        "generations_count": 3,
        "price": 119,
        "is_active": True,
    },
    {
        "name": "⭐ Популярный",
        "description": "Самый выгодный выбор",
        "generations_count": 5,
        "price": 179,
        "is_active": True,
    },
    {
        "name": "🔥 Максимальный",
        "description": "Лучшая цена за генерацию",
        "generations_count": 10,
        "price": 299,
        "is_active": True,
    },
]


async def seed():
    from db.uow import SQLAlchemyUnitOfWork
    from sqlalchemy import select

    async with SQLAlchemyUnitOfWork() as uow:
        # 1. Проверяем, есть ли уже данные
        res = await uow.session.execute(select(AiModel).filter_by(name="MockGenerator"))
        if res.scalars().first():
            print("⚠️ Database already seeded. Skipping...")
            return

        print("🌱 Seeding database with initial data...")
        
        # 2. AI Model
        ai_model = AiModel(name="MockGenerator", provider="mock", is_current=True)
        uow.session.add(ai_model)
        await uow.session.flush()

        # 3. Templates
        for t in TEMPLATES:
            template = Template(
                name=t["name"],
                category=t["category"],
                base_prompt=t["base_prompt"],
                negative_prompt=t["negative_prompt"],
                status=t["status"],
                ai_model_id=ai_model.id,
            )
            uow.session.add(template)

        # 4. Packs
        for p in PACKS:
            pack = Pack(
                name=p["name"],
                description=p["description"],
                generations_count=p["generations_count"],
                price=p["price"],
                prices_by_currency={"RUB": float(p["price"])},
                is_active=p["is_active"],
            )
            uow.session.add(pack)
        
    print(f"✅ Successfully seeded {len(TEMPLATES)} templates and {len(PACKS)} packs.")


if __name__ == "__main__":
    asyncio.run(seed())
