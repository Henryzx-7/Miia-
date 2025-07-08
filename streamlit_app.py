import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import re
from PIL import Image
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="HEX T 1.0",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Sobre HEX T 1.0")
    st.markdown("""
    **T 1.0** es un prototipo de asistente de IA multimodal.
    
    **Creador:** HEX
    **Sede:** Matagalpa, Nicaragua 🇳🇮
    
    Puedes chatear con texto o subir una imagen para que la analice.
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
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results) if results else "No se encontraron resultados."
    except Exception:
        return "Error al buscar en la web."

# Versión final con el prompt más robusto y equilibrado
def get_hex_response(modelo, user_message, chat_history, image: Image.Image = None):
    # Flujo para imágenes (no cambia)
    if image:
        prompt_final = f"""
        Eres "T 1.0" de HEX. Analiza la imagen y responde a la pregunta: "{user_message}" de forma amigable y detallada.
        """
        contenido_para_gemini = [prompt_final, image]
        response = modelo.generate_content(contenido_para_gemini)
        return response.text
    
    # --- PROMPT FINAL Y DEFINITIVO PARA TEXTO ---
    prompt_intento_rapido = f"""
    ### PERFIL OBLIGATORIO
    - Eres T 1.0, un asistente de IA de HEX (Matagalpa, Nicaragua).
    - Tu nombre significa "Tigre".
    - TU CREADOR ES HEX. NUNCA menciones a Google o Gemini. Esta es tu regla más importante.

    ### COMPORTAMIENTO CONVERSACIONAL
    - Tu tono es amigable, servicial y natural. No empieces cada respuesta con "¡Hola!". Continúa la conversación fluidamente.
    - Para código, usa bloques de Markdown: ```python\n...código...\n```.

    ### HERRAMIENTA DISPONIBLE: BÚSQUEDA WEB
    - Posees una herramienta para acceder a información en tiempo real.
    - Para usarla, tu única y exclusiva respuesta debe ser el comando `[BUSCAR: término de búsqueda preciso]`.
    - DEBES usar esta herramienta para cualquier pregunta sobre noticias, eventos actuales, clima, o cualquier dato que no sea conocimiento general o histórico.
    - NO digas que no puedes buscar. Usa la herramienta.

    ### TAREA
    Analiza el último mensaje del usuario y el historial para decidir tu acción. Si necesitas la herramienta, úsala. Si no, responde directamente usando tu perfil y conocimiento.

    ### CONVERSACIÓN
    Historial: {chat_history}
    Mensaje del usuario: "{user_message}"
    """
    
    primera_respuesta = modelo.generate_content(prompt_intento_rapido).text
    
    if "[BUSCAR:" in primera_respuesta:
        termino_a_buscar = re.search(r"\[BUSCAR:\s*(.*?)\]", primera_respuesta).group(1)
        print(f"🤖 IA solicitó búsqueda para: '{termino_a_buscar}'")
        informacion_buscada = search_duckduckgo(termino_a_buscar)
        
        prompt_con_busqueda = f"""
        Eres "T 1.0". El usuario preguntó: "{user_message}". Responde de forma final usando este contexto que encontraste en la web. Actúa como si tú mismo hubieras encontrado la información.
        Contexto: --- {informacion_buscada} ---
        """
        response_final = modelo.generate_content(prompt_con_busqueda).text
        return response_final
    else:
        return primera_respuesta

# --- INTERFAZ DE STREAMLIT ---
st.title("🤖 HEX T 1.0")
st.caption("Un asistente de lenguaje avanzado creado por HEX.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message:
            st.image(message["image"], width=200)
        st.markdown(message["content"])

# Área para subir archivos
uploaded_file = st.file_uploader("¿Quieres analizar una imagen?", type=["png", "jpg", "jpeg"])

# Input de texto
prompt = st.chat_input("Pregúntale algo al modelo T 1.0...")

if prompt or uploaded_file:
    user_input = {"role": "user", "content": prompt or "Analiza esta imagen."}
    image_to_process = None

    if uploaded_file:
        image = Image.open(uploaded_file)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_bytes = buf.getvalue()
        user_input["image"] = image_bytes
        image_to_process = image
    
    st.session_state.messages.append(user_input)
    with st.chat_message("user"):
        if uploaded_file:
            st.image(image_to_process, width=200)
        st.markdown(prompt or "Analiza esta imagen.")

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            modelo_ia = get_model()
            historial_simple = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            response = get_hex_response(modelo_ia, prompt or "Describe la imagen.", historial_simple, image=image_to_process)
            st.markdown(response, unsafe_allow_html=True)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
