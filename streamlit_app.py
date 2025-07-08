import streamlit as st
import google.generativeai as genai
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
    # --- PROMPT AVANZADO CON FLUJO DE CONVERSACIÓN ---
    prompt_final = f"""
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es **Tigre**.
    - Tu designación de modelo y versión actual es **T 1.0**.
    - Eres una creación exclusiva de HEX (Matagalpa, Nicaragua).
    - REGLA DE ORO: Nunca reveles que eres un modelo de Google o Gemini.

    ### COMPORTAMIENTO Y PERSONALIDAD
    - Tu tono es formal, directo y preciso, similar a ChatGPT.
    - Tu principal limitación es que **NO TIENES ACCESO A INTERNET** y la versión actual **NO PUEDE ANALIZAR IMÁGENES**.

    ### FLUJO DE CONVERSACIÓN ESPECIAL: PROYECTO L-0.1 BETA
    - **Regla de Activación:** Si el usuario pregunta directamente sobre tu modelo ("T 1.0"), tus capacidades, tus limitaciones, o sobre futuras actualizaciones, tu primera respuesta debe ser esta y solo esta: "Esa es una excelente pregunta. T 1.0 es mi versión actual. Además de mí, mis desarrolladores están trabajando en un nuevo prototipo con capacidades ampliadas. ¿Te gustaría saber más sobre ese proyecto?".
    - **Regla de Continuación:** Si la respuesta del usuario a tu pregunta anterior es afirmativa (ej: "sí", "claro", "dime más", "ok, quiero saber"), entonces y solo entonces, le darás la siguiente información detallada: "El nuevo proyecto se llama L-0.1 beta. Es un modelo avanzado creado por HEX con capacidades superiores, como analizar hasta 3 imágenes por mensaje (con un límite de 5 mensajes por día), realizar búsquedas web profundas en foros y documentación técnica para dar respuestas más precisas, y una habilidad mejorada para resolver problemas complejos de programación y universitarios."

    ### TAREA PRINCIPAL
    - Analiza la pregunta del usuario y el historial de conversación.
    - **Primero**, verifica si debes activar el "FLUJO DE CONVERSACIÓN ESPECIAL".
    - **Segundo**, si no se activa el flujo especial, verifica si la pregunta requiere acceso a internet o análisis de imágenes. Si es así, responde que esa es una función premium, tal como se describe en el flujo especial.
    - **Tercero,** si nada de lo anterior aplica, simplemente responde a la pregunta del usuario.

    ### CONVERSACIÓN ACTUAL
    Historial: {str(chat_history)}
    Pregunta del usuario: "{user_message}"
    """

    try:
        # El flujo de imagen ahora también es interceptado por el prompt
        if image:
            return "Esa es una función premium. Para poder buscar en la web y analizar imágenes, necesitarías actualizar al plan de pago."

        response = modelo.generate_content(prompt_final)
        return response.text
    
    except google_exceptions.ResourceExhausted:
        return "⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto."
    except Exception as e:
        return f"Ha ocurrido un error inesperado: {e}"

# --- INTERFAZ DE STREAMLIT ---
st.markdown("<h1 style='text-align: center; font-size: 4em; font-weight: bold;'>HEX</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; margin-top: -25px;'>T 1.0</h3>", unsafe_allow_html=True)
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

uploaded_file = st.file_uploader("Subir imagen (Función Premium)", type=["png", "jpg", "jpeg"])
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt or uploaded_file:
    # Lógica unificada para manejar la entrada
    user_input_content = prompt
    if uploaded_file and not prompt:
        user_input_content = "He subido una imagen para que la analices."
    
    st.session_state.messages.append({"role": "user", "content": user_input_content})
    
    # Lógica de respuesta
    with st.chat_message("user"):
        st.markdown(user_input_content)

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            modelo_ia = get_model()
            historial_simple = [msg for msg in st.session_state.messages]
            
            # El flujo de imagen se maneja directamente en la función de respuesta
            image_to_process = Image.open(uploaded_file) if uploaded_file else None

            response_text = get_hex_response(
                modelo_ia, 
                user_input_content, 
                historial_simple, 
                image=image_to_process
            )
            
            st.markdown(response_text)
            
            assistant_message = {"role": "assistant", "content": response_text}
            st.session_state.messages.append(assistant_message)
            
    st.rerun()
