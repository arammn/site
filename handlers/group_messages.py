"""Group message handlers – filters service messages, processes games, ignore commands."""
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes, CommandHandler
from database import Database
from auction import AuctionManager
from lucky_draw import LuckyDrawManager
from dice_game import DiceGameManager
from guess_number import GuessNumberManager
from .admin_private import status_public
import logging

logger = logging.getLogger(__name__)

db = Database()
auction_mgr = AuctionManager()
lucky_mgr = LuckyDrawManager()
dice_mgr = DiceGameManager()
guess_mgr = GuessNumberManager()

async def group_msg_handler(update: Update, context):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        await db.upsert_group(chat.id, chat.title or f"Group {chat.id}", chat.type)

    msg = update.effective_message
    if not msg: return
    # Skip service messages (joins, leaves)
    if msg.new_chat_members or msg.left_chat_member or msg.group_chat_created or msg.migrate_to_chat_id:
        return

    if msg.entities:
        for e in msg.entities:
            if e.type == "bot_command":
                return

    if not await db.any_game_active():
        if hash(msg.message_id) % 10 == 0:
            logger.debug(f"[GROUP] idle msg from {update.effective_user.id}")
        return

    logger.info(f"[GROUP] msg from {update.effective_user.id} in {chat.id}, paid_stars={getattr(msg,'paid_star_count',0)}")
    await auction_mgr.process_bid(update, context)
    await lucky_mgr.process_message(update, context)
    await dice_mgr.process_message(update, context)
    await guess_mgr.process_message(update, context)

# ── Ignore commands (chat admins only) ──
async def ignore_cmd(update: Update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(chat_id, user.id)
        if member.status not in ('administrator', 'creator'):
            await update.message.reply_text("⛔ Только администраторы могут использовать эту команду.")
            return
    except: return

    if not context.args:
        await update.message.reply_text("Использование: /ignore user_id")
        return
    try:
        target_id = int(context.args[0])
        await db.add_ignored_user(chat_id, target_id)
        await update.message.reply_text(f"🚫 Пользователь {target_id} добавлен в игнорируемые.")
    except ValueError:
        await update.message.reply_text("❌ Укажите числовой ID пользователя.")

async def unignore_cmd(update: Update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(chat_id, user.id)
        if member.status not in ('administrator', 'creator'): return
    except: return

    if not context.args:
        await update.message.reply_text("Использование: /unignore user_id")
        return
    try:
        target_id = int(context.args[0])
        await db.remove_ignored_user(chat_id, target_id)
        await update.message.reply_text(f"✅ Пользователь {target_id} удалён из игнорируемых.")
    except ValueError:
        await update.message.reply_text("❌ Укажите числовой ID пользователя.")

async def ignoredlist_cmd(update: Update, context):
    chat_id = update.effective_chat.id
    ids = await db.get_ignored_list(chat_id)
    if not ids:
        await update.message.reply_text("📭 Список игнорируемых пуст.")
    else:
        await update.message.reply_text("🚫 Игнорируемые:\n" + "\n".join(f"<code>{uid}</code>" for uid in ids), parse_mode="HTML")

async def grp_status(update: Update, context):
    chat = update.effective_chat
    if update.my_chat_member.new_chat_member.status in ["member", "administrator"]:
        logger.info(f"Added to {chat.title} ({chat.id})")
        await db.upsert_group(chat.id, chat.title or f"Group {chat.id}", chat.type)
        try: await context.bot.send_message(chat.id, "👋 Бот активирован! Используйте /start в личке для управления ивентами.")
        except: pass

def register_group_handlers(app):
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, group_msg_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, grp_status))
    app.add_handler(CommandHandler("status", status_public))
    app.add_handler(CommandHandler("ignore", ignore_cmd))
    app.add_handler(CommandHandler("unignore", unignore_cmd))
    app.add_handler(CommandHandler("ignoredlist", ignoredlist_cmd))
