# utils.py
from datetime import datetime
from babel.dates import format_date
from langdetect import detect, LangDetectException

def get_formatted_date(user_prompt: str) -> str:
    """
    Detecta el idioma del prompt y devuelve la fecha actual formateada en ese idioma.
    """
    try:
        # Detecta el idioma (ej: 'es', 'en', 'pt')
        lang = detect(user_prompt)
    except LangDetectException:
        lang = 'es' # Si no puede detectar, usa español por defecto

    # Mapeo de códigos de idioma a locales de Babel
    locale_map = {
        'es': 'es_ES',
        'en': 'en_US',
        'pt': 'pt_BR',
        # Puedes añadir más idiomas aquí
    }
    locale = locale_map.get(lang, 'es_ES') # Usa español si el idioma no está en el mapa

    now = datetime.now()
    # 'EEEE' para el día completo, 'd' para el día, 'MMMM' para el mes, 'y' para el año
    formatted_date = format_date(now, format='EEEE, d MMMM y', locale=locale)

    # Diccionario de respuestas por idioma
    response_map = {
        'es': f"Hoy es {formatted_date}.",
        'en': f"Today is {formatted_date}.",
        'pt': f"Hoje é {formatted_date}."
    }

    return response_map.get(lang, f"Hoy es {formatted_date}.")

def generate_chat_name(first_prompt):
    """Genera un nombre corto para el chat."""
    name = str(first_prompt).split('\n')[0]
    return name[:30] + "..." if len(name) > 30 else name
