"""Telegram bot runner: long-polling + kirim pesan nyata via Bot API.

Jalankan: python -m scripts.telegram_bot
"""
import asyncio
import html as html_mod

import httpx

from app.modules.identity.auth_service import AuthService
from app.shared.config import get_settings
from app.shared.logging import get_logger, setup_logging

setup_logging()
logger = get_logger("telegram.bot")

API = "https://api.telegram.org"


class TelegramClient:
    def __init__(self) -> None:
        s = get_settings()
        self.token = s.telegram_bot_token
        self.base = f"{API}/bot{self.token}"

    async def send(self, chat_id: int, text: str, keyboard: list | None = None) -> bool:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if keyboard:
            payload["reply_markup"] = {"inline_keyboard": keyboard}
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.post(f"{self.base}/sendMessage", json=payload)
                ok = r.status_code == 200
                if not ok:
                    logger.error("tg_send_failed", status=r.status_code, body=r.text[:150])
                return ok
        except httpx.HTTPError as e:
            logger.error("tg_send_error", error=str(e))
            return False

    async def get_updates(self, offset: int | None) -> list[dict]:
        params = {"timeout": 25}
        if offset:
            params["offset"] = offset
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.get(f"{self.base}/getUpdates", params=params)
                return r.json().get("result", []) if r.status_code == 200 else []
        except httpx.HTTPError as e:
            logger.warning("tg_getupdates_error", error=str(e))
            await asyncio.sleep(3)
            return []


def esc(s: str) -> str:
    return html_mod.escape(s)


HELP = """Perintah tersedia:
/feed — rekomendasi teratas untukmu
/help — bantuan"""


async def handle_command(client: TelegramClient, chat_id: int, text: str) -> None:
    from sqlalchemy import text as sql

    from app.infrastructure.database import async_session_factory
    from app.modules.recommendation.service import RecommendationService

    cmd = text.split()[0].split("@")[0]
    # Deep-link dulu: /start <jwt-token> (coba anggap argumen sebagai token)
    if cmd == "/start" and len(text.split()) > 1:
        token = text.split()[1]
        uid = AuthService.verify_token(token)
        if uid:
            async with async_session_factory() as s:
                await s.execute(
                    sql("UPDATE users SET telegram_id = :tid WHERE id = :uid"),
                    {"tid": chat_id, "uid": uid},
                )
                await s.commit()
            await client.send(
                chat_id, "✅ Telegram terhubung! Kamu akan terima digest & reminder."
            )
            return
        # argumen bukan token valid → jatuh ke sapaan normal

    if cmd == "/start":
        await client.send(
            chat_id,
            "Halo! Aku Peluang.ai bot.\nAku bantu temukan beasiswa, lomba, magang "
            "yang layak kamu kejar.\n\n" + HELP,
        )
        return
    if cmd == "/help":
        await client.send(chat_id, HELP)
        return

    if cmd == "/feed":
        async with async_session_factory() as s:
            row = await s.execute(
                sql("SELECT id FROM users WHERE telegram_id = :tid"), {"tid": chat_id}
            )
            uid = row.scalar()
            if not uid:
                await client.send(
                    chat_id,
                    "Akun belum terhubung. Daftar di web, lalu buka halaman profil "
                    "untuk menghubungkan Telegram.",
                )
                return
            feed = await RecommendationService(s).get_feed(uid, limit=5)
        if not feed:
            await client.send(chat_id, "Belum ada rekomendasi. Generate dulu lewat web.")
            return
        lines = ["<b>Rekomendasi teratas:</b>", ""]
        for i, f in enumerate(feed, 1):
            dl = f.get("end_date") or "-"
            lines.append(f"{i}. <b>{esc(f['title'][:70])}</b>")
            lines.append(f"   [{esc(str(f['category']))}] deadline {dl}")
        await client.send(chat_id, "\n".join(lines))
        return

    await client.send(chat_id, "Perintah tidak dikenal. " + HELP)


async def main() -> None:
    client = TelegramClient()
    if not client.token:
        logger.error("TELEGRAM_BOT_TOKEN kosong")
        return
    logger.info("telegram_bot_started", mode="long-polling")
    offset = None
    while True:
        updates = await client.get_updates(offset)
        for u in updates:
            offset = u["update_id"] + 1
            msg = u.get("message") or u.get("edited_message")
            if not msg:
                continue
            chat_id = msg["chat"]["id"]
            text = (msg.get("text") or "").strip()
            if not text:
                continue
            await handle_command(client, chat_id, text)


if __name__ == "__main__":
    asyncio.run(main())
