import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import re
from PIL import Image
import io
from google.api_core import exceptions as google_exceptions

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="centered")

# --- INYECTAR CSS PARA CAMBIOS VISUALES ---
st.markdown("""
<style>
    /* Cambia el color de fondo de los mensajes del usuario */
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-user"]) {
        background-color: #2b313e;
    }
</style>
""", unsafe_allow_html=True)


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

    ### TAREA PRINCIPAL: Decidir entre RESPONDER y BUSCAR
    1.  ACCIÓN: RESPONDER: Para la mayoría de las preguntas (conversación, conocimiento general, etc.), escribe la respuesta directamente.
    2.  ACCIÓN: BUSCAR: Para preguntas que requieran información en tiempo real (noticias, clima, etc.), responde única y exclusivamente con el comando `[BUSCAR: término de búsqueda]`.

    ### EJEMPLOS
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

# --- NUEVO INPUT CON COLUMNAS ---
col1, col2 = st.columns([1, 8])

with col1:
    uploaded_file = st.file_uploader("Cargar Imagen", label_visibility="collapsed", type=["png", "jpg", "jpeg"])

with col2:
    prompt = st.chat_input("Pregúntale algo a T 1.0...")

# --- LÓGICA DE PROCESAMIENTO DE ENTRADA ---
if prompt or uploaded_file:
    image_to_process = None
    display_prompt = prompt or "Analiza esta imagen."
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_bytes = buf.getvalue()
        user_input = {"role": "user", "content": display_prompt, "image": image_bytes}
        image_to_process = image
    else:
        user_input = {"role": "user", "content": display_prompt}

    st.session_state.messages.append(user_input)
    with st.chat_message("user"):
        if image_to_process:
            st.image(image_to_process, width=200)
        st.markdown(display_prompt)

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            modelo_ia = get_model()
            historial_simple = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            
            response_text, response_sources = get_hex_response(
                modelo_ia,
                display_prompt,
                historial_simple,
                image=image_to_process
            )
            
            st.markdown(response_text)
            if response_sources:
                with st.expander("Fuentes Consultadas"):
                    for source in response_sources:
                        st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")
            
            assistant_message = {"role": "assistant", "content": response_text, "sources": response_sources}
            st.session_state.messages.append(assistant_message)
