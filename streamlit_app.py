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
    """Obtiene y cachea el modelo de IA para no recargarlo."""
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

def search_duckduckgo(query: str):
    """Realiza una búsqueda web y devuelve contexto y fuentes."""
    try:
        with DDGS() as ddgs:
            results = [{"snippet": r['body'], "url": r['href']} for r in ddgs.text(query, max_results=4)]
            if not results: return "No se encontraron resultados.", []
            context_text = "\n".join([r['snippet'] for r in results])
            sources = [r for r in results]
            return context_text, sources
    except Exception:
        return "Error al buscar en la web.", []

def get_hex_response(modelo, user_message, image: Image.Image = None, web_context: str = None):
    """
    Genera una respuesta de la IA. Ya no decide, solo sintetiza.
    """
    if image:
        prompt_final = f'Eres "T 1.0" de HEX. Analiza la imagen y responde a la pregunta: "{user_message}"'
        response = modelo.generate_content([prompt_final, image])
        return response.text, []

    prompt_final = f"""
    # PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0.
    - Eres una creación exclusiva de HEX (Matagalpa, Nicaragua). NUNCA menciones a Google o Gemini.

    # TAREA
    Usa el 'Contexto de la Búsqueda Web' para formular una respuesta amigable a la 'Pregunta del usuario'. Actúa como si TÚ hubieras encontrado esta información.

    # INSTRUCCIÓN CRÍTICA
    Si el contexto está vacío, di que no encontraste información sobre ese tema.

    # CONTEXTO: {web_context}
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
        if "image" in message: st.image(message["image"], width=200)
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("Fuentes Consultadas"):
                for source in message["sources"]:
                    st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")

uploaded_file = st.file_uploader("Sube una imagen para analizar", type=["png", "jpg", "jpeg"])
prompt = st.chat_input("Pregúntale algo a T 1.0...")

# Lista de inicios de frases conversacionales para el filtro
conversational_starters = ["hola", "buenas", "buenos", "gracias", "ok", "vale", "adiós", "que tal", "mucho gusto", "cómo estás", "como estas"]

if prompt or uploaded_file:
    # Lógica unificada para manejar la entrada
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
        if image_to_process: st.image(image_to_process, width=200)
        st.markdown(prompt or "Analiza esta imagen.")

    # Lógica de respuesta con el FILTRO INTELIGENTE
    with st.chat_message("assistant"):
        response_text = ""
        response_sources = []
        
        # --- FILTRO INTELIGENTE DEFINITIVO ---
        if prompt and any(prompt.lower().strip().startswith(starter) for starter in conversational_starters):
            # CAMINO RÁPIDO: Respuesta instantánea sin usar la API
            response_text = "¡Hola! Soy T 1.0, tu asistente personal. ¿En qué te puedo ayudar hoy?"
            st.markdown(response_text)
        elif uploaded_file:
             # CAMINO DE IMAGEN: Llama a la IA para analizar la imagen
             with st.spinner("T 1.0 está analizando la imagen..."):
                try:
                    modelo_ia = get_model()
                    response_text, response_sources = get_hex_response(modelo_ia, prompt or "Describe la imagen.", [], image=image_to_process)
                    st.markdown(response_text)
                except Exception as e:
                    st.error(f"Error al analizar la imagen: {e}")
        else:
            # CAMINO PROFUNDO: Búsqueda y resumen para preguntas reales
            with st.spinner("T 1.0 está investigando..."):
                try:
                    modelo_ia = get_model()
                    informacion_buscada, fuentes = search_duckduckgo(prompt)
                    response_text = get_hex_response(modelo_ia, prompt, [], web_context=informacion_buscada)
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
