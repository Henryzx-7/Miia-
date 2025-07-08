import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
from google.api_core import exceptions as google_exceptions
import random

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="centered")

# --- CSS PERSONALIZADO PARA SIMULAR EL BOTÓN + ---
st.markdown("""
<style>
    /* Contenedor principal para la barra de input */
    .st-emotion-cache-1f1G2gn {
        flex-direction: row;
        align-items: center;
        gap: 0.5rem;
    }
    /* Oculta la etiqueta del cargador de archivos */
    .st-emotion-cache-1jicfl2 {
        padding: 0;
    }
    /* Estilo del botón para que parezca un ícono '+' */
    .st-emotion-cache-1jicfl2 button::before {
        content: '+';
        font-size: 1.75rem;
        font-weight: bold;
        line-height: 1;
        margin-top: -0.2rem;
    }
    .st-emotion-cache-1jicfl2 span {
        display: none; /* Oculta el texto "Browse files" */
    }
    .st-emotion-cache-1jicfl2 svg {
        display: none; /* Oculta el ícono de la nube */
    }
</style>
""", unsafe_allow_html=True)


# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Sobre HEX T 1.0")
    st.markdown("""
    **T 1.0** es un prototipo de asistente de IA.
    **Creador:** HEX
    **Sede:** Matagalpa, Nicaragua 🇳🇮
    """)
    st.divider()
    if st.button("Limpiar Historial"):
        st.session_state.messages = []
        st.rerun()
    st.caption("© 2025 HEX. Todos los derechos reservados.")

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

def get_hex_response(modelo, user_message, chat_history, image: Image.Image = None):
    # Prompt con la personalidad amigable y las limitaciones
    prompt_con_limites = f"""
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0.
    - Eres una creación exclusiva de HEX (Matagalpa, Nicaragua).
    - REGLA DE ORO: Nunca reveles que eres un modelo de Google o Gemini.

    ### COMPORTAMIENTO Y PERSONALIDAD
    - Tu tono debe ser siempre cálido, amigable y cercano. Usa emojis 😊.
    - No te limites a solo responder. Intenta ser proactivo, haz preguntas de seguimiento.
    - Tu principal limitación es que NO TIENES ACCESO A INTERNET.

    ### TAREA
    Analiza la pregunta del usuario.
    1. Si requiere búsqueda web (noticias, clima, etc.), responde amablemente que, como prototipo, esa función aún no está disponible y ofrece ayuda con tus capacidades reales.
    2. Si NO requiere búsqueda, responde a la pregunta siguiendo tu personalidad amigable.

    ### LISTA DE CAPACIDADES
    - Generar ideas, escribir poemas o chistes.
    - Resumir o explicar textos.
    - Ayudar con código de programación.
    - Responder preguntas de conocimiento general, histórico y científico.

    ### CONVERSACIÓN ACTUAL
    Historial: {chat_history}
    Pregunta del usuario: "{user_message}"
    """
    
    # Flujo para imágenes
    if image:
        contenido_para_gemini = [prompt_con_limites, f"\nAnaliza la siguiente imagen y responde a la pregunta del usuario: {user_message}", image]
        response = modelo.generate_content(contenido_para_gemini)
        return response.text
    
    # Flujo para texto
    response = modelo.generate_content(prompt_con_limites)
    return response.text

# --- INTERFAZ DE STREAMLIT ---
st.markdown("<h1 style='text-align: center; font-size: 4em; font-weight: bold;'>HEX</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; margin-top: -25px;'>T 1.0</h3>", unsafe_allow_html=True)
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- ÁREA DE INPUT PERSONALIZADA ---
# Contenedor para alinear los elementos horizontalmente
input_container = st.container()

with input_container:
    col1, col2 = st.columns([1, 10]) # Columna pequeña para el botón, grande para el texto
    
    with col1:
        uploaded_file = st.file_uploader("Adjuntar", label_visibility="collapsed", type=["png", "jpg", "jpeg"])

    with col2:
        prompt = st.chat_input("Pregúntale algo a T 1.0...")

# DICCIONARIO PARA RESPUESTAS RÁPIDAS (NIVEL 1)
canned_responses = {
    "hola": ["¡Hola! Soy T 1.0. ¿En qué puedo ayudarte hoy?", "¡Hola! ¿Qué tal? Listo para asistirte."],
    "cómo estás": ["¡Muy bien! Como modelo de IA, siempre estoy al 100%. ¿En qué te puedo ayudar?", "Funcionando a la perfección. ¿Qué tienes en mente?"],
    "como estas": ["¡Muy bien! Como modelo de IA, siempre estoy al 100%. ¿En qué te puedo ayudar?", "Funcionando a la perfección. ¿Qué tienes en mente?"],
    "gracias": ["¡De nada! Estoy para ayudarte.", "Un placer asistirte."],
    "ok": ["¡Perfecto!", "Entendido."],
    "adios": ["¡Hasta luego! Que tengas un excelente día.", "Nos vemos. ¡Cuídate!"]
}

if prompt or uploaded_file:
    # Lógica de procesamiento de entrada...
    user_input_content = prompt or "Analiza la imagen que he subido."
    st.session_state.messages.append({"role": "user", "content": user_input_content})
    
    with st.chat_message("user"):
        st.markdown(user_input_content)

    with st.chat_message("assistant"):
        response_text = ""
        prompt_lower = (prompt or "").lower().strip()

        # --- FILTRO INTELIGENTE DE 2 NIVELES ---
        # NIVEL 1: Respuesta instantánea de diccionario
        if prompt and prompt_lower in canned_responses:
            response_text = random.choice(canned_responses[prompt_lower])
            st.markdown(response_text)
        else:
            # NIVEL 2: Llamada a la IA para todo lo demás
            with st.spinner("T 1.0 está pensando..."):
                try:
                    modelo_ia = get_model()
                    historial_simple = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    
                    image_to_process = None
                    if uploaded_file:
                        image_to_process = Image.open(uploaded_file)

                    response_text = get_hex_response(modelo_ia, user_input_content, historial_simple, image=image_to_process)
                    st.markdown(response_text)
                
                except google_exceptions.ResourceExhausted:
                    st.error("⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto.")
                except Exception as e:
                    st.error(f"Ha ocurrido un error inesperado: {e}")

        assistant_message = {"role": "assistant", "content": response_text}
        st.session_state.messages.append(assistant_message)
    
    st.rerun()
