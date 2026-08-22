import asyncio
import json
import uuid

from sqlalchemy import text

from app.infrastructure.database import async_session_factory

SOURCES = [
    {
        "name": "Beasiswa LPDP",
        "source_type": "web",
        "source_url": "https://www.lpdp.kemenkeu.go.id",
        "access_method": "crawl4ai",
        "crawl_frequency": "daily",
    },
    {
        "name": "Kampus Merdeka",
        "source_type": "web",
        "source_url": "https://kampusmerdeka.kemdikbud.go.id",
        "access_method": "crawl4ai",
        "crawl_frequency": "daily",
    },
    {
        "name": "RSS Lomba Mahasiswa",
        "source_type": "rss",
        "source_url": "https://example.com/lomba-feed.xml",
        "access_method": "rss",
        "crawl_frequency": "hourly",
    },
]

OPPORTUNITIES = [
    {
        "title": "Beasiswa LPDP 2026 Tahap 1",
        "slug": "beasiswa-lpdp-2026-tahap-1",
        "url": "https://www.lpdp.kemenkeu.go.id/beasiswa-2026-tahap-1",
        "category": "beasiswa",
        "organizer": "Kementerian Keuangan RI",
        "location": "Seluruh Indonesia",
        "description": "Beasiswa penuh untuk studi S2/S3 dalam dan luar negeri.",
        "end_date": "2026-03-31",
    },
    {
        "title": "Magang Bersertifikat Kampus Merdeka Batch 8",
        "slug": "magang-kampus-merdeka-batch-8",
        "url": "https://kampusmerdeka.kemdikbud.go.id/magang-batch-8",
        "category": "magang",
        "organizer": "Kemdikbudristek",
        "location": "Seluruh Indonesia",
        "description": "Program magang 6 bulan di perusahaan mitra dengan konversi SKS.",
        "end_date": "2026-02-28",
    },
    {
        "title": "Kompetisi Data Science Nasional 2026",
        "slug": "kompetisi-data-science-2026",
        "url": "https://example.com/kompetisi-ds-2026",
        "category": "lomba",
        "organizer": "Universitas Indonesia",
        "location": "Jakarta",
        "description": "Kompetisi analisis data untuk mahasiswa S1 seluruh Indonesia.",
        "prize": "Total hadiah Rp 100.000.000",
        "end_date": "2026-04-15",
    },
    {
        "title": "Fellowship Riset AI Indonesia",
        "slug": "fellowship-riset-ai-indonesia",
        "url": "https://example.com/fellowship-ai",
        "category": "fellowship",
        "organizer": "BRIN",
        "location": "Bandung",
        "description": "Fellowship riset 3 bulan di bidang AI untuk mahasiswa S2.",
        "end_date": "2026-05-01",
    },
    {
        "title": "Konferensi Teknologi Mahasiswa Nasional",
        "slug": "konferensi-teknologi-mahasiswa-2026",
        "url": "https://example.com/konferensi-teknologi",
        "category": "konferensi",
        "organizer": "ITB",
        "location": "Bandung",
        "description": "Konferensi tahunan presentasi paper teknologi oleh mahasiswa.",
        "end_date": "2026-06-30",
    },
    {
        "title": "Volunteer Mengajar Desa Digital",
        "slug": "volunteer-mengajar-desa-digital",
        "url": "https://example.com/volunteer-desa-digital",
        "category": "volunteer",
        "organizer": "Kominfo",
        "location": "Jawa Tengah",
        "description": "Program volunteer literasi digital di desa-desa selama 2 minggu.",
        "end_date": "2026-03-15",
    },
    {
        "title": "Pelatihan Cloud Computing Gratis",
        "slug": "pelatihan-cloud-computing-2026",
        "url": "https://example.com/pelatihan-cloud",
        "category": "pelatihan",
        "organizer": "Google Developer Student Club",
        "location": "Online",
        "description": "Pelatihan gratis Google Cloud Platform untuk mahasiswa.",
        "end_date": "2026-02-20",
    },
    {
        "title": "Beasiswa Unggulan Kemendikbud 2026",
        "slug": "beasiswa-unggulan-kemendikbud-2026",
        "url": "https://example.com/beasiswa-unggulan",
        "category": "beasiswa",
        "organizer": "Kemdikbudristek",
        "location": "Seluruh Indonesia",
        "description": "Beasiswa S1/S2/S3 untuk mahasiswa berprestasi.",
        "end_date": "2026-07-31",
    },
    {
        "title": "Lomba Business Plan Nasional",
        "slug": "lomba-business-plan-nasional-2026",
        "url": "https://example.com/lomba-bisnis-plan",
        "category": "lomba",
        "organizer": "Universitas Gadjah Mada",
        "location": "Yogyakarta",
        "description": "Kompetisi rencana bisnis untuk mahasiswa dengan mentoring.",
        "prize": "Total hadiah Rp 50.000.000",
        "end_date": "2026-04-30",
    },
    {
        "title": "Program Riset Mahasiswa BRIN",
        "slug": "program-riset-mahasiswa-brin-2026",
        "url": "https://example.com/riset-brin",
        "category": "riset",
        "organizer": "BRIN",
        "location": "Seluruh Indonesia",
        "description": "Pendanaan riset mahasiswa S1/S2 di laboratorium BRIN.",
        "end_date": "2026-08-31",
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

        for i, opp in enumerate(OPPORTUNITIES):
            from datetime import date as date_type

            end_date = (
                date_type.fromisoformat(opp["end_date"]) if opp.get("end_date") else None
            )
            await session.execute(
                text(
                    "INSERT INTO opportunities (id, source_id, title, slug, url, category, organizer, location, description, prize, end_date, status) "
                    "VALUES (:id, :source_id, :title, :slug, :url, :category, :organizer, :location, :description, :prize, :end_date, 'active')"
                ),
                {
                    "id": uuid.uuid4(),
                    "source_id": source_ids[i % len(source_ids)],
                    "prize": opp.get("prize"),
                    "end_date": end_date,
                    **{k: v for k, v in opp.items() if k != "end_date"},
                },
            )

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
                "VALUES (:user_id, :education_level, :major, :university, :graduation_year, :cgpa, :skills, :interests, :goals, :location)"
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
        print(f"Seeded: {len(SOURCES)} sources, {len(OPPORTUNITIES)} opportunities, 1 user.")


if __name__ == "__main__":
    asyncio.run(seed())
