import os
import time
import logging
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ApplicationBuilder  # Nuevo en v20+
)
from telegram.constants import ChatAction

# Configuración básica
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext) -> None:
    """Manejador del comando /start"""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await update.message.reply_text('✅ Bot funcionando correctamente!')

def main() -> None:
    """Función principal para iniciar el bot"""
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TOKEN:
        logger.error("No se encontró TELEGRAM_TOKEN en las variables de entorno")
        return

    # Configuración nueva para v20+
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Registramos los manejadores
    application.add_handler(CommandHandler("start", start))
    
    logger.info("Bot iniciado, esperando mensajes...")
    application.run_polling()

if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            logger.error(f"Error crítico: {e}. Reiniciando en 30 segundos...")
            time.sleep(30)