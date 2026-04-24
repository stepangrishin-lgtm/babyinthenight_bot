import asyncio
import os
import random
import json

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ChatAction
from aiogram.types import ReactionTypeEmoji

# ===== НАСТРОЙКИ =====

TOKEN = "8593782765:AAG0LDK9AJfQx2u-zs16MxYJAqJm1tEhbTg"

TRIGGERS = [
    "малышка на ночь",
    "доброй ночи с малышкой",
]

DELAY_MIN = 10
DELAY_MAX = 40

SCORE_MIN = 5
SCORE_MAX = 10

EXTRA_COMMENT_PROB = 0.03
REPLY_ATTACK_PROB = 0.08
TROLL_PROB = 0.2

EASTER_EGG_PROB = 0.02
RARE_EGG_PROB = 0.005
LEGENDARY_EGG_PROB = 0.001

REMEMBER_PROB = 0.05
RECALL_PROB = 0.1

MEMORY_FILE = "memory.json"

REACTION_PROB = 0.07  # 7% шанс реакции

# =====================

replied_media_groups: set[str] = set()


# ===== ПАМЯТЬ =====

def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {}

    if "girls" not in data:
        data["girls"] = []

    return data


def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)


def remember_user(memory, user_id):
    user = memory.get(str(user_id), {"seen": 0})
    user["seen"] += 1
    memory[str(user_id)] = user


def remember_girl(memory, text):
    if not text:
        return

    memory["girls"].append({
        "text": text[:100],
        "score": random.randint(7, 10)
    })

    memory["girls"] = memory["girls"][-10:]


def recall_girl(memory):
    if not memory["girls"]:
        return None

    girl = random.choice(memory["girls"])

    phrases = [
        f"этот станок мне знаком... тогда было {girl['score']}/10",
        f"где-то я уже это видел... примерно на {girl['score']}/10",
        f"у меня есть запись похожего случая: {girl['score']}/10",
        f"похожа на мою бывшую... всей комиссией оценивали на {girl['score']}/10",
    ]

    return random.choice(phrases)


# ===== ПАСХАЛКИ =====

def easter_egg():
    eggs = [
        "Оценка: 47/10. Вердикт: комиссия в ахуе.",
        "Система перегружена. Повторите малышку позже.",
        "Оценки нет, но есть фулл...",
        "⚠️ превышен допустимый уровень малышки",
        "так, я звоню ее маме",
        "Стоп, это че Серега?",
    ]
    return random.choice(eggs)


def rare_easter_egg():
    eggs = [
        "это уже уровень выше моего понимания",
        "мне нужно подумать",
        "я это запомню",
        "кто-то сегодня постарался",
    ]
    return random.choice(eggs)


async def legendary_easter_egg(message: Message):
    sequences = [
        ["...", "подожди", "это было слишком сильно", "я не готов"],
        ["система анализирует", "система перегружена", "система сдалась"],
        ["я всё понял", "но лучше вам этого не знать"],
    ]

    seq = random.choice(sequences)

    for line in seq:
        await asyncio.sleep(random.randint(1, 3))
        await message.reply(line)


# ===== ОСНОВНОЙ ОТВЕТ =====

def make_reply():
    score = random.randint(SCORE_MIN, SCORE_MAX)

    verdicts = [
        "рабочий станок",
        "норм, но дрочить я уже не буду",
        "результат почти как у Лехи",
        "достойный уровень",
        "ночная смена одобряет",
    ]

    templates = [
        "Оценка {score}/10. Вердикт: {verdict}.",
        "{score}/10. Вердикт комиссии: {verdict}.",
        "Итог: {score}/10 — {verdict}.",
    ]

    return random.choice(templates).format(
        score=score,
        verdict=random.choice(verdicts)
    )


def troll_text(name):
    variants = [
        f"{name}, мда, жалкое зрелище",
        f"{name}, не старайся",
        f"{name}, мне и твоим родителям звонить?",
        f"{name}, как же жидко ты всрался",
    ]
    return random.choice(variants)


async def typing(bot, chat_id):
    await bot.send_chat_action(chat_id, ChatAction.TYPING)


# ===== ЛОГИКА =====

async def maybe_reply(message: Message, bot: Bot):
    text = (message.text or message.caption or "").lower()

    if not any(t in text for t in TRIGGERS):
        return

    # альбом → один ответ
    mgid = message.media_group_id
    if mgid:
        if mgid in replied_media_groups:
            return
        replied_media_groups.add(mgid)

    await asyncio.sleep(random.randint(DELAY_MIN, DELAY_MAX))
    await typing(bot, message.chat.id)

    memory = load_memory()

    if message.from_user:
        remember_user(memory, message.from_user.id)

    save_memory(memory)

    # ===== ПАСХАЛКИ =====
    roll = random.random()

    if roll < LEGENDARY_EGG_PROB:
        await legendary_easter_egg(message)
        return

    elif roll < LEGENDARY_EGG_PROB + RARE_EGG_PROB:
        await message.reply(rare_easter_egg())
        return

    elif roll < LEGENDARY_EGG_PROB + RARE_EGG_PROB + EASTER_EGG_PROB:
        await message.reply(easter_egg())
        return

    # ===== ВСПОМИНАНИЕ =====
    if random.random() < RECALL_PROB:
        recall = recall_girl(memory)
        if recall:
            await message.reply(recall)

    # ===== ОСНОВНОЙ ОТВЕТ =====
    await message.reply(make_reply())

    # ===== ЗАПОМИНАНИЕ =====
    if random.random() < REMEMBER_PROB:
        remember_girl(memory, message.text or message.caption)
        save_memory(memory)
        await asyncio.sleep(1)
        await message.reply("я это запомню")

    # ===== ТРОЛЛИНГ =====
    if random.random() < TROLL_PROB and memory:
        user_id = random.choice(list(memory.keys()))
        name = f"@user{str(user_id)[-4:]}"
        await asyncio.sleep(1)
        await message.reply(troll_text(name))

    # ===== СЦЕНКА =====
    if random.random() < EXTRA_COMMENT_PROB:
        await asyncio.sleep(2)
        await message.reply("ой, да тут же всё плохо")
        await asyncio.sleep(3)
        await message.reply("а нет, показалось")


# ===== ОТВЕТ НА ОТВЕТ =====

async def reply_attack(message: Message, bot: Bot):
    if not message.reply_to_message:
        return

    if message.reply_to_message.from_user and message.reply_to_message.from_user.id == bot.id:
        if random.random() < REPLY_ATTACK_PROB:
            await asyncio.sleep(1)
            await message.reply("А я вроде тебя и не спрашивал")


async def random_reaction(message: Message):
    if not message.from_user:
        return

    # не реагируем на себя
    if message.from_user.is_bot:
        return

    if random.random() > REACTION_PROB:
        return

    emojis = ["💩", "🤡", "🔥"]

    try:
        await message.react([
            ReactionTypeEmoji(emoji=random.choice(emojis))
        ])
    except:
        pass  # если реакция не поддерживается — игнор


# ===== MAIN =====

async def main():
    if not TOKEN:
        raise RuntimeError("Не задан TOKEN")

    bot = Bot(TOKEN)
    dp = Dispatcher()

    dp.message.register(maybe_reply, F.text | F.caption)
    dp.message.register(maybe_reply, F.forward_date | F.forward_from | F.forward_from_chat)

    dp.message.register(reply_attack)
    dp.message.register(random_reaction)

    print("BOT STARTED")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
