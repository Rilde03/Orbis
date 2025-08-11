import os
import time
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.constants import ChatAction  # Import modificado para versión 20.x+

# Configuración básica de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    """Manejador del comando /start"""
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    update.message.reply_text('✅ Bot funcionando correctamente!')

def main() -> None:
    """Función principal para iniciar el bot"""
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TOKEN:
        logger.error("No se encontró TELEGRAM_TOKEN en las variables de entorno")
        return

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    # Registramos el manejador de comandos
    dispatcher.add_handler(CommandHandler("start", start))
    
    logger.info("Bot iniciado, esperando mensajes...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            logger.error(f"Error crítico: {e}. Reiniciando en 30 segundos...")
            time.sleep(30)