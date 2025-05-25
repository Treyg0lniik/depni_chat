from warnings import filters
from telegram.ext import Application, CommandHandler, filters, MessageHandler
from config import BOT_TOKEN
from game import create_room
from handlers import admin_broadcast, cmd_give, register_handlers, start, daily, top, backup

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("backup", backup))
    register_handlers(app)
    app.add_handler(CommandHandler("dap", create_room))
    app.add_handler(CommandHandler("give", cmd_give))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, admin_broadcast))


    print("Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    # адрес вашего Render-сервиса: 
    # например https://depni-chat-bot.onrender.com
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  
    WEBHOOK_PATH = f"/{os.getenv('WEBHOOK_SECRET')}"
    
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_URL + WEBHOOK_PATH,
    )
