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

DELAY_MIN = 10
DELAY_MAX = 40

SCORE_MIN = 5
SCORE_MAX = 10

# Маленькая вероятность "сценки" (например 3%)
EXTRA_COMMENT_PROB = 0.03

# Задержка между двумя сообщениями сценки
EXTRA_COMMENT_DELAY_MIN = 2
EXTRA_COMMENT_DELAY_MAX = 6

# =====================

replied_media_groups: set[str] = set()


def make_reply() -> str:
    score = random.randint(SCORE_MIN, SCORE_MAX)

    # Можно оставлять вердикты "по качеству", но т.к. оценки теперь 5–10,
    # достаточно диапазонов 5–6, 7–8, 9–10.
    verdicts_by_score = {
        (5, 6): [
            "работает, и это главное",
            "условно годится (но мне нравится)",
            "можно брать",
            "норм, без трагедий",
        ],
        (7, 8): [
            "рабочий станок",
            "принято в эксплуатацию",
            "годится на ночную смену",
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

    # 1) Случайная задержка "обдумывания"
    await asyncio.sleep(random.randint(DELAY_MIN, DELAY_MAX))

    # Основной ответ
    await message.reply(make_reply())

    # 3) Редкая "сценка" с двумя сообщениями
    if random.random() < EXTRA_COMMENT_PROB:
        # первое сообщение
        await message.reply("бля, да у неё хуй!")

        # пауза
        await asyncio.sleep(random.randint(EXTRA_COMMENT_DELAY_MIN, EXTRA_COMMENT_DELAY_MAX))

        # второе сообщение
        await message.reply("зато какой...")


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
