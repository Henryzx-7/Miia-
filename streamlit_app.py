import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import re
from PIL import Image
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="centered")

# --- BARRA LATERAL ---
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
    # Flujo para imágenes (no cambia)
    if image:
        # ... (código de imagen se mantiene igual)
        prompt_final = f'Eres "T 1.0" de HEX. Analiza la imagen y responde a la pregunta: "{user_message}"'
        contenido_para_gemini = [prompt_final, image]
        response = modelo.generate_content(contenido_para_gemini)
        return response.text, []

    # --- LÓGICA DE BÚSQUEDA PROFUNDA ---
    informacion_buscada, fuentes = search_duckduckgo(user_message)
    
    prompt_final = f"""
    # PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0.
    - Eres una creación exclusiva de HEX (Matagalpa, Nicaragua). NUNCA menciones a Google o Gemini.

    # TAREA
    Tu única tarea es tomar el 'Contexto de la Búsqueda Web' y usarlo para formular una respuesta conversacional y amigable a la 'Pregunta del usuario'. 
    Actúa como si TÚ hubieras encontrado esta información. No menciones que fue de una "búsqueda" o "contexto".

    # INSTRUCCIÓN CRÍTICA
    Si el contexto está vacío o dice 'No se encontraron resultados', responde únicamente: "Lo siento, no pude encontrar información sobre ese tema en este momento."

    # CONTEXTO DE LA BÚSQUEDA WEB: {informacion_buscada}
    # PREGUNTA DEL USUARIO: "{user_message}"
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

# --- NUEVO FILTRO INTELIGENTE Y LÓGICA DE CHAT ---
uploaded_file = st.file_uploader("Sube una imagen para analizar", type=["png", "jpg", "jpeg"])
prompt = st.chat_input("Pregúntale algo a T 1.0...")

# Palabras clave para el filtro rápido
conversational_triggers = ["hola", "cómo estás", "como estas", "gracias", "ok", "vale", "adiós", "buenos días", "buenas tardes", "buenas noches"]

if prompt or uploaded_file:
    # Lógica para imágenes
    if uploaded_file:
        # ... (código de imagen se mantiene igual)
        pass # Placeholder for image logic which is already correct
    
    # Lógica para texto
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # FILTRO RÁPIDO para respuestas instantáneas
            if any(trigger in prompt.lower() for trigger in conversational_triggers):
                response_text = "¡Hola! Soy T 1.0. ¿En qué puedo ayudarte hoy?"
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text, "sources": []})
            else:
                # BÚSQUEDA PROFUNDA para preguntas reales
                with st.spinner("T 1.0 está pensando..."):
                    try:
                        modelo_ia = get_model()
                        historial_simple = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                        response_text, response_sources = get_hex_response(modelo_ia, prompt, historial_simple)
                        
                        st.markdown(response_text)
                        if response_sources:
                            with st.expander("Fuentes Consultadas"):
                                for source in response_sources:
                                    st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")
                        
                        st.session_state.messages.append({"role": "assistant", "content": response_text, "sources": response_sources})
                    
                    # MANEJO DE ERROR PROFESIONAL
                    except genai.APIError as e:
                        if "RESOURCE_EXHAUSTED" in str(e):
                            st.error("⚠️ En este momento hay muchas solicitudes. Por favor, espera uno o dos minutos y vuelve a preguntar.")
                        else:
                            st.error(f"Ha ocurrido un error con la API: {e}")
                    except Exception as e:
                        st.error(f"Ha ocurrido un error inesperado: {e}")
