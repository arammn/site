from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import random

# Словарь для хранения пользователей и их групп
groups = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для игры 'Секретный Санта'. "
        "Добавь участников с помощью команды /join и начнем игру!"
    )

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user.first_name

    if chat_id not in groups:
        groups[chat_id] = []

    if user in groups[chat_id]:
        await update.message.reply_text(f"{user}, ты уже в игре!")
    else:
        groups[chat_id].append(user)
        await update.message.reply_text(f"{user} добавлен в список участников!")

async def list_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in groups or not groups[chat_id]:
        await update.message.reply_text("Нет участников. Добавьте их с помощью /join.")
    else:
        participants = "\n".join(groups[chat_id])
        await update.message.reply_text(f"Участники:\n{participants}")

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in groups or len(groups[chat_id]) < 2:
        await update.message.reply_text("Для начала игры нужно как минимум 2 участника!")
        return

    participants = groups[chat_id]
    random.shuffle(participants)
    
    # Создаем пары
    pairs = {participants[i]: participants[(i + 1) % len(participants)] for i in range(len(participants))}

    for giver, receiver in pairs.items():
        user_id = [u.id for u in context.bot_data['users'] if u.first_name == giver][0]
        await context.bot.send_message(chat_id=user_id, text=f"Ты даришь подарок {receiver}!")

    groups[chat_id] = []  # Очищаем участников после игры
    await update.message.reply_text("Игра началась! Участники получили свои задания в личные сообщения.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    groups[chat_id] = []
    await update.message.reply_text("Список участников очищен.")

# Создаем приложение
app = ApplicationBuilder().token("7921269365:AAH_CrY9SeEGmoJKrmzWd6aqWwIOlu40bj0").build()

# Обработчики
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("list", list_participants))
app.add_handler(CommandHandler("startgame", start_game))
app.add_handler(CommandHandler("reset", reset))

print("Бот запущен!")
app.run_polling()
