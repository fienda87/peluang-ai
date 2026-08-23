import asyncio
import json
import uuid
from datetime import date, timedelta

from sqlalchemy import text

from app.infrastructure.database import async_session_factory


def future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


SOURCES = [
    {
        "name": "LPDP Kemenkeu",
        "source_type": "web",
        "source_url": "https://lpdp.kemenkeu.go.id/",
        "access_method": "http",
        "crawl_frequency": "daily",
    },
    {
        "name": "Djarum Beasiswa Plus",
        "source_type": "web",
        "source_url": "https://djarumbeasiswaplus.org/",
        "access_method": "http",
        "crawl_frequency": "weekly",
    },
    {
        "name": "Tanoto Foundation",
        "source_type": "web",
        "source_url": "https://www.tanotofoundation.org/en/scholarship/",
        "access_method": "http",
        "crawl_frequency": "weekly",
    },
    {
        "name": "Beasiswa Indo (aggregator)",
        "source_type": "web",
        "source_url": "https://beasiswaindo.com/",
        "access_method": "http",
        "crawl_frequency": "daily",
    },
]


TEST_USER = {
    "email": "test@peluang.ai",
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User",
    "auth_provider": "local",
}

TEST_PROFILE = {
    "education_level": "S1",
    "major": "Teknik Informatika",
    "university": "Universitas Indonesia",
    "graduation_year": 2027,
    "cgpa": 3.75,
    "skills": ["Python", "Machine Learning", "Data Analysis"],
    "interests": ["beasiswa", "magang", "riset"],
    "goals": ["S2 luar negeri", "karir di tech"],
    "location": "Jakarta",
}


async def seed() -> None:
    async with async_session_factory() as session:
        result = await session.execute(text("SELECT count(*) FROM sources"))
        if result.scalar() > 0:
            print("Database already seeded, skipping.")
            return

        source_ids = []
        for src in SOURCES:
            sid = uuid.uuid4()
            source_ids.append(sid)
            await session.execute(
                text(
                    "INSERT INTO sources (id, name, source_type, source_url, access_method, crawl_frequency) "
                    "VALUES (:id, :name, :source_type, :source_url, :access_method, :crawl_frequency)"
                ),
                {"id": sid, **src},
            )

        # Opportunity TIDAK di-seed lagi — data asli datang dari pipeline
        # scraping (python -m scripts.crawl_once).

        existing_user = await session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": TEST_USER["email"]},
        )
        user_id = existing_user.scalar_one_or_none()
        if not user_id:
            user_id = uuid.uuid4()
            await session.execute(
                text(
                    "INSERT INTO users (id, email, username, first_name, last_name, auth_provider) "
                    "VALUES (:id, :email, :username, :first_name, :last_name, :auth_provider)"
                ),
                {"id": user_id, **TEST_USER},
            )
        await session.execute(
            text(
                "INSERT INTO user_profiles (user_id, education_level, major, university, graduation_year, cgpa, skills, interests, goals, location) "
                "VALUES (:user_id, :education_level, :major, :university, :graduation_year, :cgpa, :skills, :interests, :goals, :location) "
                "ON CONFLICT (user_id) DO UPDATE SET education_level = EXCLUDED.education_level, "
                "major = EXCLUDED.major, university = EXCLUDED.university, graduation_year = EXCLUDED.graduation_year, "
                "cgpa = EXCLUDED.cgpa, skills = EXCLUDED.skills, interests = EXCLUDED.interests, "
                "goals = EXCLUDED.goals, location = EXCLUDED.location"
            ),
            {
                "user_id": user_id,
                "skills": json.dumps(TEST_PROFILE["skills"]),
                "interests": json.dumps(TEST_PROFILE["interests"]),
                "goals": json.dumps(TEST_PROFILE["goals"]),
                **{k: v for k, v in TEST_PROFILE.items() if k not in ("skills", "interests", "goals")},
            },
        )

        await session.commit()
        print(f"Seeded: {len(SOURCES)} sources, 1 user. Jalankan crawl_once untuk data asli.")


if __name__ == "__main__":
    asyncio.run(seed())
