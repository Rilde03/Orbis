# Configuración esencial
TELEGRAM_TOKEN = "7561609533:AAEh1IzS_U79nYBdOtgtf-O5cJDvDbqPkuY"
ADMIN_CHAT_ID = 5356844745
OPENROUTER_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyArTZFg0DZtR-aF0dfxYdzmIgrtCMUmSL4"
MODEL_IA = "meta-llama/llama-3-70b-instruct"

# Configuración básica
DATOS_INICIALES = {
    "nombre_bot": "Aiorbis",
    "version": "2.0",
    "creador": "TuNombre",
    "fecha_creacion": "10/08/2024",
    "modos_activos": ["normal", "debate", "académico"],
    "ia_predeterminada": "gemini",
    "estadisticas": {
        "consultas_totales": 0,
        "consultas_hoy": 0,
        "errores": 0
    }
}

MENSAJES = {
    "bienvenida": "Bot Aiorbis v2.0\nUsa /menu para ver opciones",
    "error": "Error procesando tu solicitud",
    "acceso_denegado": "Comando solo disponible para administradores"
}