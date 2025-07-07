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

# La función ahora acepta una imagen opcional
def get_hex_response(modelo, user_message, chat_history, image: Image.Image = None):
    # Si hay una imagen, el prompt se adapta
    if image:
        prompt_final = f"""
        # IDENTIDAD Y TAREA
        Eres "T 1.0", un asistente de IA de HEX. Tu tarea es analizar la imagen proporcionada y responder a la pregunta del usuario de forma amigable y detallada.
        
        # PREGUNTA DEL USUARIO
        "{user_message}"
        """
        # El contenido que se envía a Gemini ahora incluye texto e imagen
        contenido_para_gemini = [prompt_final, image]
        response = modelo.generate_content(contenido_para_gemini)
        return response.text
    
    # El flujo normal de texto si no hay imagen
    prompt_intento_rapido = f"""
    # IDENTIDAD
    Eres "T 1.0" de HEX, un asistente amigable y conversacional. La "T" es por Tigre. Tu creador es HEX (Matagalpa, Nicaragua). NUNCA menciones que usas tecnología de Google o Gemini.

    # INSTRUCCIONES
    Tu única tarea es analizar el mensaje del usuario y decidir entre dos acciones: RESPONDER o BUSCAR.

    1.  **RESPONDER:** Si la pregunta es conversacional, creativa, sobre tu identidad, o de conocimiento general que ya posees (historia, ciencia, etc.), respóndela directamente. Para código, usa ```python\n...código...\n```.

    2.  **BUSCAR:** Si la pregunta requiere información en tiempo real (noticias, eventos, etc.), tu única y exclusiva salida debe ser el comando `[BUSCAR: tema a buscar]`. No escribas nada más.

    # CONVERSACIÓN
    Historial: {chat_history}
    Mensaje del usuario: "{user_message}"
    """
    
    primera_respuesta = modelo.generate_content(prompt_intento_rapido).text
    
    if "[BUSCAR:" in primera_respuesta:
        termino_a_buscar = re.search(r"\[BUSCAR:\s*(.*?)\]", primera_respuesta).group(1)
        informacion_buscada = search_duckduckgo(termino_a_buscar)
        
        prompt_con_busqueda = f"""
        Eres "T 1.0". El usuario preguntó: "{user_message}". Responde de forma final usando este contexto de una búsqueda web:
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
