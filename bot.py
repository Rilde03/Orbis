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

# Configuración de logging mejorada
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuración desde variables de entorno con validación
def get_env_var(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and value is None:
        logger.error(f"Falta la variable de entorno requerida: {name}")
        raise ValueError(f"La variable de entorno {name} es requerida")
    return value

TELEGRAM_TOKEN = get_env_var('TELEGRAM_TOKEN', required=True)
ADMIN_CHAT_ID = int(get_env_var('ADMIN_CHAT_ID', '0'))
OPENROUTER_API_KEY = get_env_var('OPENROUTER_API_KEY')
GEMINI_API_KEY = get_env_var('GEMINI_API_KEY')
MODEL_IA = get_env_var('MODEL_IA', 'meta-llama/llama-3-70b-instruct')
PORT = int(get_env_var('PORT', '10000'))

# Configuración de modos mejorada
MODOS_DISPONIBLES = {
    "normal": {"nombre": "Normal", "desc": "Respuestas equilibradas"},
    "debate": {"nombre": "Debate", "desc": "Postura crítica y argumentativa"},
    "gracioso": {"nombre": "Gracioso", "desc": "Respuestas con humor"},
    "académico": {"nombre": "Académico", "desc": "Respuestas formales con referencias"}
}

IAS_DISPONIBLES = {
    "gemini": {"nombre": "Gemini", "requiere_key": GEMINI_API_KEY is not None},
    "openrouter": {"nombre": "OpenRouter", "requiere_key": OPENROUTER_API_KEY is not None}
}

# Validación de configuraciones de IA disponibles
IAS_ACTIVAS = {k: v for k, v in IAS_DISPONIBLES.items() if v["requiere_key"]}
if not IAS_ACTIVAS:
    logger.error("No hay servicios de IA configurados correctamente")
    raise ValueError("Al menos un servicio de IA debe estar configurado (Gemini u OpenRouter)")

class ServicioIA:
    @staticmethod
    async def generar_respuesta(ia_seleccionada, modo, consulta, es_inline=False):
        """Genera respuesta usando el servicio de IA seleccionado"""
        sistemas = {
            "normal": "Responde de forma clara y completa." + (" Máximo 200 palabras." if es_inline else ""),
            "debate": "Analiza críticamente y refuta puntos clave. Sé contundente pero educado." + (" Máximo 300 palabras." if es_inline else ""),
            "gracioso": "Responde con humor inteligente, sin chistes forzados." + (" Máximo 80 palabras." if es_inline else ""),
            "académico": "Responde formalmente con conceptos relevantes. Cita fuentes brevemente si es necesario." + (" Máximo 300 palabras." if es_inline else "")
        }
        
        sistema = sistemas.get(modo, sistemas["normal"])
        
        try:
            if ia_seleccionada == "gemini" and IAS_DISPONIBLES["gemini"]["requiere_key"]:
                respuesta = await ServicioIA._generar_gemini(modo, sistema, consulta, es_inline)
                return respuesta, None
            elif ia_seleccionada == "openrouter" and IAS_DISPONIBLES["openrouter"]["requiere_key"]:
                respuesta = await ServicioIA._generar_openrouter(modo, sistema, consulta, es_inline)
                return respuesta, None
            else:
                # Fallback a la primera IA disponible
                for ia, config in IAS_ACTIVAS.items():
                    respuesta = await ServicioIA._generar_respuesta_ia(ia, modo, sistema, consulta, es_inline)
                    if respuesta:
                        return respuesta, None
                return "No hay servicios de IA disponibles en este momento", "No hay IAs configuradas"
        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            return f"Error procesando tu consulta. Por favor intenta nuevamente.", str(e)

    @staticmethod
    async def _generar_gemini(modo, sistema, consulta, es_inline):
        """Genera respuesta usando Gemini API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': GEMINI_API_KEY
            }
            
            prompt = f"Eres Aiorbis. Modo: {modo}. {sistema}\nConsulta: {consulta}"
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                headers=headers,
                json=data,
                timeout=10 if es_inline else 30
            )
            response.raise_for_status()
            
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.error(f"Error en Gemini: {str(e)}")
            raise

    @staticmethod
    async def _generar_openrouter(modo, sistema, consulta, es_inline):
        """Genera respuesta usando OpenRouter API"""
        try:
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
                timeout=10 if es_inline else 30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Error en OpenRouter: {str(e)}")
            raise

class BotManager:
    def __init__(self):
        self.application = None
        self.modos_activos = {"normal"}  # Solo modo normal por defecto
        self.ia_seleccionada = next(iter(IAS_ACTIVAS.keys()))  # Primera IA disponible

    async def iniciar(self):
        """Inicia el bot con configuración adecuada para Render"""
        try:
            self.application = (
                ApplicationBuilder()
                .token(TELEGRAM_TOKEN)
                .http_version("1.1")
                .get_updates_http_version("1.1")
                .build()
            )
            
            self._configurar_handlers()
            
            logger.info("Iniciando bot multi-modo...")
            
            # Configuración para Render
            await self.application.initialize()
            await self.application.start()
            
            if os.getenv('RENDER'):
                # En Render, usamos webhook
                url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TELEGRAM_TOKEN}"
                await self.application.bot.setWebhook(url)
                logger.info(f"Webhook configurado en: {url}")
            else:
                # Localmente, usamos polling
                await self.application.updater.start_polling()
                logger.info("Usando polling para updates")
            
            # Mantener la aplicación corriendo
            while True:
                await asyncio.sleep(3600)
                
        except Exception as e:
            logger.error(f"Error al iniciar el bot: {e}")
            raise
        finally:
            await self._apagar_bot()

    async def _apagar_bot(self):
        """Apaga el bot de manera limpia"""
        if self.application:
            logger.info("Apagando bot...")
            try:
                await self.application.stop()
                await self.application.shutdown()
            except Exception as e:
                logger.error(f"Error al apagar el bot: {e}")

    def _configurar_handlers(self):
        """Configura todos los handlers del bot"""
        dp = self.application
        
        # Handlers de comandos
        dp.add_handler(CommandHandler('start', self._mostrar_menu))
        dp.add_handler(CommandHandler('menu', self._mostrar_menu))
        dp.add_handler(CommandHandler('modos', self._mostrar_modos))
        dp.add_handler(CommandHandler('ia', self._mostrar_ia))
        dp.add_handler(CommandHandler('status', self._mostrar_status))
        
        # Handlers de interacción
        dp.add_handler(CallbackQueryHandler(self._manejar_callbacks))
        dp.add_handler(InlineQueryHandler(self._inline_query))
        
        # Handler de mensajes regulares
        dp.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Chat(chat_id=ADMIN_CHAT_ID),
            self._procesar_mensaje
        ))
        
        # Manejo de errores
        dp.add_error_handler(self._manejar_errores)

    async def _mostrar_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú principal"""
        if not self._es_admin(update):
            return
            
        modos_activos = ", ".join([MODOS_DISPONIBLES[m]["nombre"] for m in self.modos_activos])
        
        keyboard = [
            [InlineKeyboardButton("⚙️ Cambiar Modos", callback_data='modos_menu')],
            [InlineKeyboardButton("🧠 Cambiar IA", callback_data='ia_menu')],
            [InlineKeyboardButton("📊 Status", callback_data='status')],
            [InlineKeyboardButton("❌ Cerrar", callback_data='cerrar')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        mensaje = (
            f"🤖 <b>Aiorbis Multi-Modo</b>\n\n"
            f"🔧 <b>Modos activos:</b> {modos_activos}\n"
            f"🧠 <b>IA seleccionada:</b> {IAS_DISPONIBLES[self.ia_seleccionada]['nombre']}\n\n"
            "💡 Usa @{context.bot.username} en cualquier chat para consultas inline"
        )
        
        await self._responder_o_editar(update, mensaje, reply_markup)

    async def _mostrar_modos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra la interfaz de selección de modos"""
        keyboard = []
        for modo, config in MODOS_DISPONIBLES.items():
            estado = "✅" if modo in self.modos_activos else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    f"{estado} {config['nombre']}",
                    callback_data=f"modo_{modo}"
                )
            ])
            
        keyboard.append([InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')])
        
        mensaje = "⚙️ <b>Configuración de modos de respuesta:</b>\n" + \
                 "\n".join([f"{config['nombre']}: {config['desc']}" for modo, config in MODOS_DISPONIBLES.items()])
        
        await self._responder_o_editar(update, mensaje, InlineKeyboardMarkup(keyboard))

    async def _mostrar_ia(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra la interfaz de selección de IA"""
        keyboard = []
        for ia, config in IAS_ACTIVAS.items():
            estado = "✅" if ia == self.ia_seleccionada else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    f"{estado} {config['nombre']}",
                    callback_data=f"ia_{ia}"
                )
            ])
            
        keyboard.append([InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')])
        
        mensaje = "🧠 <b>Selección de Modelo de IA:</b>\n" + \
                 "\n".join([f"{config['nombre']}" for ia, config in IAS_ACTIVAS.items()])
        
        await self._responder_o_editar(update, mensaje, InlineKeyboardMarkup(keyboard))

    async def _mostrar_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el estado actual del bot"""
        if not self._es_admin(update):
            return
            
        modos_activos = "\n".join([f"• {MODOS_DISPONIBLES[m]['nombre']}" for m in self.modos_activos])
        
        mensaje = (
            f"📊 <b>Estado del Bot</b>\n\n"
            f"<b>Modos activos:</b>\n{modos_activos}\n\n"
            f"<b>IA seleccionada:</b> {IAS_DISPONIBLES[self.ia_seleccionada]['nombre']}\n"
            f"<b>Modelo:</b> {MODEL_IA}\n\n"
            f"<i>Última actualización: {time.strftime('%Y-%m-%d %H:%M:%S')}</i>"
        )
        
        await self._responder_o_editar(update, mensaje)

    async def _manejar_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja todas las interacciones con botones inline"""
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
            
        elif data == 'status':
            await self._mostrar_status(update, context)
            
        elif data == 'menu_principal':
            await self._mostrar_menu(update, context)

    async def _inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja las consultas inline desde cualquier chat"""
        query = update.inline_query.query
        if not query.strip():
            return
            
        try:
            resultados = []
            for modo, config in MODOS_DISPONIBLES.items():
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
                        title=f"{config['nombre']} ({IAS_DISPONIBLES[self.ia_seleccionada]['nombre']}): {query[:20]}...",
                        input_message_content=InputTextMessageContent(
                            message_text=f"🔹 <b>{config['nombre']}</b> ({IAS_DISPONIBLES[self.ia_seleccionada]['nombre']})\n\n{respuesta}",
                            parse_mode="HTML"
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
        """Procesa mensajes de texto regulares del admin"""
        if not self._es_admin(update):
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
            
        await update.message.reply_text(respuesta, parse_mode="HTML")

    async def _manejar_errores(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja errores no capturados"""
        error = str(context.error)
        logger.error(f"Error no capturado: {error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Ocurrió un error procesando tu solicitud. Por favor intenta nuevamente.",
                parse_mode="HTML"
            )

    def _es_admin(self, update: Update) -> bool:
        """Verifica si el mensaje proviene del admin"""
        return update.effective_chat and update.effective_chat.id == ADMIN_CHAT_ID

    async def _responder_o_editar(self, update: Update, texto: str, reply_markup=None):
        """Envía o edita un mensaje según el contexto"""
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=texto,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif update.message:
            await update.message.reply_text(
                text=texto,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

async def main():
    """Función principal para iniciar el bot"""
    bot = BotManager()
    await bot.iniciar()

if __name__ == "__main__":
    # Manejo mejorado de reinicios
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("Bot detenido manualmente")
            break
        except Exception as e:
            logger.error(f"Error crítico: {e}. Reiniciando en 30 segundos...")
            time.sleep(30)