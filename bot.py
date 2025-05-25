import asyncio
from warnings import filters
from telegram.ext import Application, CommandHandler, filters, MessageHandler
from config import BOT_TOKEN
from game import create_room
from handlers import admin_broadcast, cmd_give, register_handlers, start, daily, top, backup

def main():
    app = Application.builder().token(BOT_TOKEN).build()

        # Удаляем все webhooks, чтобы избежать Conflict
    asyncio.get_event_loop().run_until_complete(
        app.bot.delete_webhook(drop_pending_updates=True)
    )
        
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("dap", create_room))
    app.add_handler(CommandHandler("give", cmd_give))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, admin_broadcast))
    register_handlers(app)

    print("Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()