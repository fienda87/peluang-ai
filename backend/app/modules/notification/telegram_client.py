"""Minimal Telegram Bot API client (kirim pesan, tanpa aiogram)."""

import httpx

from app.shared.config import get_settings
from app.shared.logging import get_logger

logger = get_logger("telegram.client")


class TelegramClient:
    def __init__(self) -> None:
        self.token = get_settings().telegram_bot_token
        self.base = f"https://api.telegram.org/bot{self.token}" if self.token else ""

    async def send(self, chat_id: int, text: str, keyboard: list | None = None) -> bool:
        if not self.base:
            logger.warning("tg_no_token")
            return False
        payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
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
