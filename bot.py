import asyncio
import os
from warnings import filters
from telegram.ext import Application, CommandHandler, filters, MessageHandler
from config import BOT_TOKEN
from game import create_room
from handlers import admin_broadcast, cmd_give, register_handlers, start, daily, top, backup
from threading import Thread
from aiohttp import web

# ——— Health-check endpoint для Render ————————————
async def health(request):
    return web.Response(text="OK")

async def run_health_server():
    app = web.Application()
    app.add_routes([web.get("/", health)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))  # Render выделит этот порт
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

def start_health_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_health_server())
    loop.run_forever()

def main():
    Thread(target=start_health_server, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    
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