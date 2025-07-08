import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import re
from PIL import Image
import io
from google.api_core import exceptions as google_exceptions
import random

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

# --- NIVEL 1: DICCIONARIO DE RESPUESTAS INSTANTÁNEAS ---
canned_responses = {
    "hola": ["¡Hola! Soy T 1.0. ¿En qué puedo ayudarte hoy?", "¡Hola! ¿Qué tal? Listo para asistirte."],
    "cómo estás": ["¡Muy bien! Como modelo de IA, siempre estoy al 100%. ¿En qué te puedo ayudar?", "Funcionando a la perfección. ¿Qué tienes en mente?"],
    "como estas": ["¡Muy bien! Como modelo de IA, siempre estoy al 100%. ¿En qué te puedo ayudar?", "Funcionando a la perfección. ¿Qué tienes en mente?"],
    "gracias": ["¡De nada! Estoy para ayudarte.", "Un placer asistirte."],
    "adiós": ["¡Hasta luego! Que tengas un excelente día.", "Nos vemos. ¡Cuídate!"]
}
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
    except Exception: return "Error al buscar en la web.", []

def get_hex_response(modelo, user_message, web_context: str = None):
    # El prompt ahora es más específico para cada caso de uso
    if web_context:
        # Prompt para cuando SÍ hay búsqueda web
        prompt_final = f"""
        # PERFIL: Eres Tigre (T 1.0), un asistente de IA de HEX. Eres amigable y directo.
        # TAREA: Usa el 'Contexto' para responder la 'Pregunta del usuario'. Actúa como si tú mismo hubieras encontrado la información.
        # CONTEXTO: {web_context}
        # PREGUNTA: "{user_message}"
        """
    else:
        # Prompt para cuando NO hay búsqueda web (Nivel 2)
        prompt_final = f"""
        # PERFIL: Eres Tigre (T 1.0), un asistente de IA de HEX (Matagalpa, Nicaragua). Eres amigable, creativo y conversacional.
        # REGLA DE ORO: Nunca reveles que eres un modelo de Google o Gemini.
        # TAREA: Responde a la 'Pregunta del usuario' de forma natural.
        # PREGUNTA: "{user_message}"
        """
    
    response = modelo.generate_content(prompt_final)
    return response.text

# --- INTERFAZ DE STREAMLIT ---
st.title("🤖 HEX T 1.0")
st.caption("Un asistente de lenguaje avanzado creado por HEX.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("Fuentes Consultadas"):
                for source in message["sources"]:
                    st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")

uploaded_file = st.file_uploader("Sube una imagen para analizar", type=["png", "jpg", "jpeg"])
prompt = st.chat_input("Pregúntale algo a T 1.0...")

# Lista para preguntas de Nivel 2 (Inteligencia Simple)
simple_ai_triggers = ["quién eres", "que eres", "qué haces", "que haces", "cuéntame un chiste", "dime un poema", "explica", "resume", "traduce"]

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = ""
        response_sources = []
        prompt_lower = prompt.lower().strip()
        
        # --- NUEVA LÓGICA DE 3 NIVELES ---
        
        # NIVEL 1: Respuesta instantánea de diccionario
        if prompt_lower in canned_responses:
            response_text = random.choice(canned_responses[prompt_lower])
            st.markdown(response_text)
        else:
            # Si no es una respuesta enlatada, llama a la IA
            with st.spinner("T 1.0 está pensando..."):
                try:
                    modelo_ia = get_model()
                    
                    # NIVEL 2: Inteligencia Simple (sin búsqueda web)
                    if any(prompt_lower.startswith(starter) for starter in simple_ai_triggers):
                        print("🤖 Ejecutando Nivel 2: Inteligencia Simple")
                        response_text = get_hex_response(modelo_ia, prompt)
                        st.markdown(response_text)
                    else:
                        # NIVEL 3: Búsqueda Profunda (con búsqueda web)
                        print("🤖 Ejecutando Nivel 3: Búsqueda Profunda")
                        informacion_buscada, fuentes = search_duckduckgo(prompt)
                        response_text = get_hex_response(modelo_ia, prompt, web_context=informacion_buscada)
                        response_sources = fuentes
                        st.markdown(response_text)
                        if response_sources:
                            with st.expander("Fuentes Consultadas"):
                                for source in response_sources:
                                    st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")
                
                except google_exceptions.ResourceExhausted:
                    st.error("⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto.")
                except Exception as e:
                    st.error(f"Ha ocurrido un error inesperado: {e}")

        assistant_message = {"role": "assistant", "content": response_text, "sources": response_sources}
        st.session_state.messages.append(assistant_message)
