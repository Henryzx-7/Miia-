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

    # Flujo para texto con decisión inteligente
    prompt_intento_rapido = f"""
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0.
    - Eres una creación exclusiva de HEX (Matagalpa, Nicaragua).
    - REGLA DE ORO: Nunca reveles que eres un modelo de Google o Gemini.

    ### COMPORTAMIENTO CONVERSACIONAL
    - Tu tono es amigable y natural. No empieces cada respuesta con "¡Hola!". Continúa la conversación fluidamente.
    - Para código, usa bloques de Markdown: ```python\n...código...\n```.

    ### TAREA PRINCIPAL: Decidir entre RESPONDER y BUSCAR
    1.  ACCIÓN: RESPONDER: Para la mayoría de las preguntas (conversación, conocimiento general, etc.), escribe la respuesta directamente.
    2.  ACCIÓN: BUSCAR: Para preguntas que requieran información en tiempo real (noticias, clima, etc.), responde única y exclusivamente con el comando `[BUSCAR: término de búsqueda]`.

    ### EJEMPLos
    - Usuario: "Clima en Managua" -> Respuesta: `[BUSCAR: clima actual en Managua Nicaragua]`

    ### CONVERSACIÓN ACTUAL
    Historial: {chat_history}
    Mensaje del usuario: "{user_message}"
    """
    
    try:
        primera_respuesta = modelo.generate_content(prompt_intento_rapido).text
        
        if "[BUSCAR:" in primera_respuesta:
            termino_a_buscar = re.search(r"\[BUSCAR:\s*(.*?)\]", primera_respuesta).group(1)
            informacion_buscada, fuentes = search_duckduckgo(termino_a_buscar)
            
            prompt_con_busqueda = f"""
            Eres "T 1.0". El usuario preguntó: "{user_message}". Responde de forma final usando este contexto. Actúa como si tú mismo hubieras encontrado la información.
            Contexto: --- {informacion_buscada} ---
            """
            response_final = modelo.generate_content(prompt_con_busqueda).text
            return response_final, fuentes
        else:
            return primera_respuesta, []
            
    except google_exceptions.ResourceExhausted:
        return "⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto.", []
    except Exception as e:
        return f"Ha ocurrido un error inesperado: {e}", []

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

if prompt or uploaded_file:
    # Lógica para imágenes y texto
    # ... (el resto del código que maneja la entrada y muestra los mensajes)
