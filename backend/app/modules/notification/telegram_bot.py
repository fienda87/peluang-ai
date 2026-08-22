from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.shared.config import get_settings
from app.shared.logging import get_logger

logger = get_logger("telegram.bot")

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    args = message.text.split()
    token = args[1] if len(args) > 1 else None

    if token:
        await message.answer(
            "Akun Telegram berhasil dihubungkan! Ketik /help untuk melihat perintah."
        )
        logger.info("telegram_linked", telegram_id=message.from_user.id)
    else:
        await message.answer(
            "Halo! Saya Peluang.ai bot.\n"
            "Saya membantu kamu menemukan beasiswa, lomba, magang, dan peluang lainnya.\n\n"
            "Ketik /feed untuk melihat rekomendasi."
        )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Perintah tersedia:\n"
        "/feed - Lihat rekomendasi peluang\n"
        "/saved - Peluang yang disimpan\n"
        "/settings - Pengaturan notifikasi"
    )


@router.message(Command("feed"))
async def cmd_feed(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Lihat Detail", url="http://localhost:3000"),
                InlineKeyboardButton(text="Simpan", callback_data="save:demo"),
            ]
        ]
    )
    await message.answer(
        "Top rekomendasi untukmu:\n\n"
        "1. Beasiswa LPDP 2026 (skor: 0.92)\n"
        "2. Magang Kampus Merdeka Batch 8 (skor: 0.85)\n"
        "3. Kompetisi Data Science Nasional (skor: 0.78)",
        reply_markup=keyboard,
    )


@router.message(Command("saved"))
async def cmd_saved(message: Message) -> None:
    await message.answer("Peluang tersimpan:\n\n(Belum ada peluang tersimpan)")


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Daily Digest: ON", callback_data="toggle:digest")],
            [InlineKeyboardButton(text="Deadline Reminder: ON", callback_data="toggle:reminder")],
        ]
    )
    await message.answer("Pengaturan notifikasi:", reply_markup=keyboard)


def create_bot() -> tuple[Bot, Dispatcher]:
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp
