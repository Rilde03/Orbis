import os
import time
import logging
import asyncio
import requests
from uuid import uuid4
from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    InlineQueryHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración desde variables de entorno
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', 0))
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MODEL_IA = os.getenv('MODEL_IA', 'meta-llama/llama-3-70b-instruct')

# Configuración de modos
MODOS_DISPONIBLES = {
    "normal": "Normal",
    "debate": "Debate",
    "gracioso": "Gracioso",
    "académico": "Académico"
}

IAS_DISPONIBLES = {
    "gemini": "Gemini",
    "openrouter": "OpenRouter"
}

DATOS_INICIALES = {
    "modos_activos": ["normal", "debate", "académico"],
    "ia_predeterminada": "gemini"
}

MENSAJES = {
    "acceso_denegado": "⚠️ Comando solo para administradores",
    "bienvenida": "🤖 Aiorbis Multi-Modo\nUsa /menu para ver opciones",
    "error": "Error procesando tu solicitud"
}

class ServicioIA:
    @staticmethod
    async def generar_respuesta(ia_seleccionada, modo, consulta, es_inline=False):
        sistemas = {
            "normal": "Responde de forma clara y completa." + (" Máximo 200 palabras." if es_inline else ""),
            "debate": "Analiza críticamente y refuta puntos clave. Sé contundente pero educado." + (" Máximo 300 palabras." if es_inline else ""),
            "gracioso": "Responde con humor inteligente, sin chistes forzados." + (" Máximo 80 palabras." if es_inline else ""),
            "académico": "Responde formalmente con conceptos relevantes. Cita fuentes brevemente si es necesario." + (" Máximo 300 palabras." if es_inline else "")
        }
        
        if ia_seleccionada == "gemini":
            respuesta, error = await ServicioIA._generar_gemini(modo, sistemas.get(modo, ""), consulta, es_inline)
            if not error:
                return respuesta, None
            logger.warning(f"Falló Gemini, intentando con OpenRouter. Error: {error}")
            return await ServicioIA._generar_openrouter(modo, sistemas.get(modo, ""), consulta, es_inline)
        else:
            return await ServicioIA._generar_openrouter(modo, sistemas.get(modo, ""), consulta, es_inline)

    @staticmethod
    async def _generar_gemini(modo, sistema, consulta, es_inline):
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': GEMINI_API_KEY
            }
            
            prompt = f"Eres Aiorbis. Modo: {modo}. {sistema}\nConsulta: {consulta}"
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            
            timeout = 10 if es_inline else 30
            
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                headers=headers,
                json=data,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"], None
        except Exception as e:
            logger.error(f"Error en Gemini: {str(e)}")
            return f"Error de conexión con Gemini (modo {modo}).", str(e)

    @staticmethod
    async def _generar_openrouter(modo, sistema, consulta, es_inline):
        try:
            timeout = 10 if es_inline else 30
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://telegram.org",
                    "X-Title": "Aiorbis-MultiMode"
                },
                json={
                    "model": MODEL_IA,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"Eres Aiorbis. Modo: {modo}. {sistema}"
                        },
                        {
                            "role": "user",
                            "content": consulta
                        }
                    ],
                    "temperature": 0.7 if modo == "gracioso" else 0.5,
                    "max_tokens": 500 if es_inline else 1500
                },
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip(), None
        except Exception as e:
            logger.error(f"Error en OpenRouter: {str(e)}")
            return f"Error procesando tu consulta en OpenRouter (modo {modo}).", str(e)

class BotManager:
    def __init__(self):
        self.application = None
        self.modos_activos = set(DATOS_INICIALES["modos_activos"])
        self.ia_seleccionada = DATOS_INICIALES["ia_predeterminada"]

    async def iniciar(self):
        """Inicia el bot con manejo adecuado del bucle de eventos"""
        try:
            self.application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
            self._configurar_handlers()
            
            logger.info("Bot multi-modo iniciado")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Mantener el bot corriendo
            while True:
                await asyncio.sleep(3600)  # Espera 1 hora
            
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error en la ejecución: {e}")
            raise
        finally:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()

    def _configurar_handlers(self):
        dp = self.application
        
        dp.add_handler(CommandHandler('start', self._mostrar_menu))
        dp.add_handler(CommandHandler('menu', self._mostrar_menu))
        dp.add_handler(CommandHandler('modos', self._mostrar_modos))
        dp.add_handler(CommandHandler('ia', self._mostrar_ia))
        
        dp.add_handler(CallbackQueryHandler(self._manejar_callbacks))
        
        dp.add_handler(InlineQueryHandler(self._inline_query))
        dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._procesar_mensaje))
        
        dp.add_error_handler(self._manejar_errores)

    async def _mostrar_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat and update.effective_chat.id != ADMIN_CHAT_ID:
            await update.message.reply_text(MENSAJES["acceso_denegado"])
            return
            
        modos_activos = ", ".join([MODOS_DISPONIBLES[m] for m in self.modos_activos])
        
        keyboard = [
            [InlineKeyboardButton("Cambiar Modos", callback_data='modos_menu')],
            [InlineKeyboardButton("Cambiar IA", callback_data='ia_menu')],
            [InlineKeyboardButton("Cerrar", callback_data='cerrar')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        mensaje = (
            f"🤖 Aiorbis Multi-Modo\n\n"
            f"🔧 Modos activos: {modos_activos}\n"
            f"🧠 IA seleccionada: {IAS_DISPONIBLES[self.ia_seleccionada]}\n\n"
            "💡 Usa @tu_bot en cualquier chat para consultas inline"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=mensaje,
                reply_markup=reply_markup
            )
            await update.callback_query.answer()
        elif update.message:
            await update.message.reply_text(
                text=mensaje,
                reply_markup=reply_markup
            )

    async def _mostrar_modos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = []
        for modo, nombre in MODOS_DISPONIBLES.items():
            estado = "✅" if modo in self.modos_activos else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    f"{estado} {nombre}",
                    callback_data=f"modo_{modo}"
                )
            ])
            
        keyboard.append([InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        mensaje = "⚙️ Configuración de modos de respuesta:"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=mensaje,
                reply_markup=reply_markup
            )
            await update.callback_query.answer()
        elif update.message:
            await update.message.reply_text(
                text=mensaje,
                reply_markup=reply_markup
            )

    async def _mostrar_ia(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = []
        for ia, nombre in IAS_DISPONIBLES.items():
            estado = "✅" if ia == self.ia_seleccionada else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    f"{estado} {nombre}",
                    callback_data=f"ia_{ia}"
                )
            ])
            
        keyboard.append([InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        mensaje = "🧠 Selección de Modelo de IA:"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=mensaje,
                reply_markup=reply_markup
            )
            await update.callback_query.answer()
        elif update.message:
            await update.message.reply_text(
                text=mensaje,
                reply_markup=reply_markup
            )

    async def _manejar_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == 'cerrar':
            await query.delete_message()
            return
            
        if data.startswith('modo_'):
            modo = data.split('_')[1]
            if modo in self.modos_activos:
                self.modos_activos.remove(modo)
            else:
                self.modos_activos.add(modo)
            await self._mostrar_modos(update, context)
            
        elif data.startswith('ia_'):
            self.ia_seleccionada = data.split('_')[1]
            await self._mostrar_ia(update, context)
            
        elif data == 'modos_menu':
            await self._mostrar_modos(update, context)
            
        elif data == 'ia_menu':
            await self._mostrar_ia(update, context)
            
        elif data == 'menu_principal':
            await self._mostrar_menu(update, context)

    async def _inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.inline_query.query
        if not query.strip():
            return
            
        try:
            resultados = []
            for modo, nombre in MODOS_DISPONIBLES.items():
                if modo not in self.modos_activos:
                    continue
                    
                respuesta, _ = await ServicioIA.generar_respuesta(
                    self.ia_seleccionada, 
                    modo, 
                    query,
                    es_inline=True
                )
                
                resultados.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title=f"{nombre} ({IAS_DISPONIBLES[self.ia_seleccionada]}): {query[:20]}...",
                        input_message_content=InputTextMessageContent(
                            message_text=f"🔹 {nombre} ({IAS_DISPONIBLES[self.ia_seleccionada]})\n\n{respuesta}"
                        ),
                        description=respuesta[:100] + ("..." if len(respuesta) > 100 else "")
                    )
                )
            
            await update.inline_query.answer(
                resultados,
                cache_time=0,
                is_personal=True
            )
            
        except Exception as e:
            logger.error(f"Error en inline query: {str(e)}")
            await update.inline_query.answer([], cache_time=0)

    async def _procesar_mensaje(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat and update.effective_chat.id != ADMIN_CHAT_ID:
            return
            
        texto = update.message.text
        
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        
        modo_actual = next(iter(self.modos_activos), "normal")
        
        respuesta, _ = await ServicioIA.generar_respuesta(
            self.ia_seleccionada,
            modo_actual,
            texto,
            es_inline=False
        )
            
        await update.message.reply_text(respuesta)

    async def _manejar_errores(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Error: {str(context.error)}")
        if update and update.effective_message:
            await update.effective_message.reply_text(MENSAJES["error"])

async def main():
    bot = BotManager()
    await bot.iniciar()

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("Bot detenido manualmente")
            break
        except Exception as e:
            logger.error(f"Error crítico: {e}. Reiniciando en 30 segundos...")
            time.sleep(30)