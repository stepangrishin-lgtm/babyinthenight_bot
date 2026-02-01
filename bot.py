import asyncio
import os
import random

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

# ===== НАСТРОЙКИ =====

TOKEN = os.getenv("BOT_TOKEN")  # либо впишите токен строкой
TRIGGERS = [
    "малышка на ночь",
    "доброй ночи с малышкой",
]

DELAY_SECONDS = 20  # ← задержка ответа

# =====================

# Чтобы не отвечать несколько раз на один альбом
replied_media_groups: set[str] = set()


def make_reply() -> str:
    score = random.randint(1, 10)

    verdicts_by_score = {
        (1, 3): [
            "не станок, а загадка",
            "лучше было не начинать",
            "в утиль без акта",
            "сомнительное инженерное решение",
        ],
        (4, 6): [
            "работает, но настораживает",
            "условно годится",
            "можно, но без энтузиазма",
            "на грани допуска",
        ],
        (7, 8): [
            "рабочий станок",
            "принято в эксплуатацию",
            "норм, можно брать",
            "без критичных дефектов",
        ],
        (9, 10): [
            "легендарный станок",
            "уровень промышленного стандарта",
            "сертифицировано ночной сменой",
            "это уже искусство",
        ],
    }

    def pick_verdict(s: int) -> str:
        for (lo, hi), items in verdicts_by_score.items():
            if lo <= s <= hi:
                return random.choice(items)
        return "неопознанный агрегат"

    verdict = pick_verdict(score)

    templates = [
        "Оценка {score}/10. Вердикт: {verdict}.",
        "{score}/10. Вердикт комиссии: {verdict}.",
        "Итоговая оценка — {score}/10. Вердикт: {verdict}.",
        "Ставлю {score}/10. Вердикт: {verdict}.",
    ]

    return random.choice(templates).format(score=score, verdict=verdict)


async def maybe_reply(message: Message) -> None:
    text = (message.text or message.caption or "").lower()

    if not any(trigger in text for trigger in TRIGGERS):
        return

    # Если это альбом — отвечаем один раз
    mgid = message.media_group_id
    if mgid:
        if mgid in replied_media_groups:
            return
        replied_media_groups.add(mgid)

    # --- имитация "размышления" ---
    await asyncio.sleep(DELAY_SECONDS)

    await message.reply(make_reply())


async def main():
    if not TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN")

    bot = Bot(TOKEN)
    dp = Dispatcher()

    # Пересланные посты
    dp.message.register(
        maybe_reply,
        (F.forward_date | F.forward_from | F.forward_from_chat),
    )

    # Копипаста / обычные сообщения
    dp.message.register(maybe_reply, F.text | F.caption)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())