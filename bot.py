import os
import time
import logging
from telegram.ext import Updater, CommandHandler
from telegram import ChatAction

# Configuración básica
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update, context):
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    update.message.reply_text('Bot funcionando correctamente!')

def main():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    updater = Updater(TOKEN, use_context=True)
    
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            logger.error(f"Error: {e}. Reiniciando en 30 segundos...")
            time.sleep(30)