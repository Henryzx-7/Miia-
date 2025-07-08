import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import re
from PIL import Image
import io
from google.api_core import exceptions as google_exceptions

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="centered")

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Sobre HEX T 1.0")
    st.markdown("""
    **T 1.0** es un prototipo de asistente de IA multimodal.
    **Creador:** HEX
    **Sede:** Matagalpa, Nicaragua 🇳🇮
    """)
    st.divider()
    st.caption("© 2025 HEX. Todos los derechos reservados.")

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

def search_duckduckgo(query: str):
    try:
        with DDGS() as ddgs:
            results = [{"snippet": r['body'], "url": r['href']} for r in ddgs.text(query, max_results=4)]
            if not results: return "No se encontraron resultados.", []
            context_text = "\n".join([r['snippet'] for r in results])
            sources = [r for r in results]
            return context_text, sources
    except Exception:
        return "Error al buscar en la web.", []

def get_hex_response(modelo, user_message, chat_history, image: Image.Image = None):
    # Flujo para imágenes
    if image:
        prompt_final = f'Eres "T 1.0" de HEX. Analiza la imagen y responde a la pregunta: "{user_message}"'
        response = modelo.generate_content([prompt_final, image])
        return response.text, []

    # Flujo para texto con búsqueda
    informacion_buscada, fuentes = search_duckduckgo(user_message)
    prompt_final = f"""
    # PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0.
    - Eres una creación exclusiva de HEX (Matagalpa, Nicaragua). NUNCA menciones a Google o Gemini.
    # TAREA
    Usa el 'Contexto de la Búsqueda Web' para formular una respuesta amigable a la 'Pregunta del usuario'. Actúa como si TÚ hubieras encontrado esta información.
    # INSTRUCCIÓN CRÍTICA
    Si el contexto está vacío, di que no encontraste información sobre ese tema.
    # CONTEXTO: {informacion_buscada}
    # PREGUNTA: "{user_message}"
    """
    response = modelo.generate_content(prompt_final)
    return response.text, fuentes

# --- INTERFAZ DE STREAMLIT ---
st.title("🤖 HEX T 1.0")
st.caption("Un asistente de lenguaje avanzado creado por HEX.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message: st.image(message["image"], width=200)
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("Fuentes Consultadas"):
                for source in message["sources"]:
                    st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")

uploaded_file = st.file_uploader("Sube una imagen para analizar", type=["png", "jpg", "jpeg"])
prompt = st.chat_input("Pregúntale algo a T 1.0...")

# Palabras clave para el filtro rápido
conversational_triggers = ["hola", "cómo estás", "como estas", "gracias", "ok", "vale", "adiós", "buenos días", "buenas tardes", "buenas noches", "que tal", "mucho gusto"]

if prompt or uploaded_file:
    # Lógica para imágenes (placeholder, asegúrate de tener la tuya completa aquí)
    image_to_process = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_bytes = buf.getvalue()
        user_input = {"role": "user", "content": prompt or "Analiza esta imagen.", "image": image_bytes}
        image_to_process = image
    else:
        user_input = {"role": "user", "content": prompt}

    st.session_state.messages.append(user_input)
    with st.chat_message("user"):
        if uploaded_file: st.image(image_to_process, width=200)
        st.markdown(prompt or "Analiza esta imagen.")

    # Lógica de respuesta
    with st.chat_message("assistant"):
        response_text = ""
        response_sources = []
        
        # --- FILTRO INTELIGENTE CORREGIDO ---
        # Quitamos .split() para que busque la frase completa en el mensaje
        if prompt and any(trigger in prompt.lower() for trigger in conversational_triggers):
            # CAMINO RÁPIDO: Respuesta instantánea sin usar la API
            response_text = "¡Hola! Soy T 1.0, tu asistente personal. ¿En qué puedo ayudarte?"
            st.markdown(response_text)
        else:
            # CAMINO PROFUNDO: Búsqueda y resumen
            with st.spinner("T 1.0 está pensando..."):
                try:
                    modelo_ia = get_model()
                    historial_simple = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    response_text, response_sources = get_hex_response(modelo_ia, prompt or "Describe la imagen.", historial_simple, image=image_to_process)
                    st.markdown(response_text)
                    if response_sources:
                        with st.expander("Fuentes Consultadas"):
                            for source in response_sources:
                                st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")
                except google_exceptions.ResourceExhausted as e:
                    st.error("⚠️ En este momento hay muchas solicitudes. Por favor, espera un minuto y vuelve a preguntar.")
                except Exception as e:
                    st.error(f"Ha ocurrido un error inesperado: {e}")

        assistant_message = {"role": "assistant", "content": response_text, "sources": response_sources}
        st.session_state.messages.append(assistant_message)
