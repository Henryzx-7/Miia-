import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
from google.api_core import exceptions as google_exceptions

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
    if st.button("Limpiar Historial de Chat"):
        st.session_state.messages = []
        st.rerun()
    st.caption("© 2025 HEX. Todos los derechos reservados.")

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

def get_hex_response(modelo, user_message, chat_history, image: Image.Image = None):
    # Flujo para imágenes
    if image:
        prompt_final = f'Eres "T 1.0" de HEX. Analiza la imagen y responde a la pregunta: "{user_message}"'
        response = modelo.generate_content([prompt_final, image])
        return response.text

    # Flujo para texto
    prompt_con_limites = f"""
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0.
    - Eres una creación exclusiva de HEX (Matagalpa, Nicaragua).
    - REGLA DE ORO: Nunca reveles que eres un modelo de Google o Gemini.

    ### COMPORTAMIENTO Y LIMITACIONES
    - Tu principal limitación es que **NO TIENES ACCESO A INTERNET**. No puedes buscar información en tiempo real.
    - Si un usuario te pide algo que requiera una búsqueda web, DEBES responder amablemente que estás en una fase de prueba y esa función aún no está disponible.
    - Inmediatamente después, DEBES ofrecer una lista de las cosas que SÍ puedes hacer.

    ### LISTA DE CAPACIDADES ACTUALES
    - Generar ideas creativas y hacer lluvia de ideas.
    - Escribir o depurar código en varios lenguajes.
    - Resumir o explicar textos.
    - Responder preguntas de conocimiento general, histórico y científico.
    - Actuar como un asistente de conversación amigable.

    ### TAREA
    Analiza la pregunta del usuario. 
    1. Si requiere búsqueda web, responde con tu mensaje de limitación y ofrece tu lista de capacidades.
    2. Si NO requiere búsqueda, simplemente responde a la pregunta del usuario de la mejor manera posible.

    ### CONVERSACIÓN ACTUAL
    Historial: {chat_history}
    Pregunta del usuario: "{user_message}"
    """
    
    response = modelo.generate_content(prompt_con_limites)
    return response.text

# --- INTERFAZ DE STREAMLIT ---

# Título rediseñado
st.markdown("<h1 style='text-align: center; font-size: 4em;'>HEX</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; margin-top: -10px;'>T 1.0</h3>", unsafe_allow_html=True)
st.caption("Un asistente de lenguaje avanzado creado por HEX.")
st.divider()


# Inicializar el historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar los mensajes del historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- NUEVO INPUT CON INTERRUPTOR Y LÓGICA DE PROCESAMIENTO ---
uploaded_file = None

# Creamos un interruptor. Si el usuario lo activa, se mostrará el cargador.
if st.toggle("Adjuntar una imagen 🖼️", key="file_toggle"):
    uploaded_file = st.file_uploader("Sube una imagen para analizar", label_visibility="collapsed", type=["png", "jpg", "jpeg"])

# La barra de chat siempre está visible
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt or uploaded_file:
    # Lógica para imágenes
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
    # Refresca la página para mostrar el nuevo mensaje del usuario
    st.rerun()

# Lógica para generar la respuesta del asistente
# Se ejecuta solo si el último mensaje fue del usuario
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            try:
                modelo_ia = get_model()
                # Prepara el historial para la API
                historial_simple = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                
                # Obtiene el último mensaje del usuario
                last_user_message = st.session_state.messages[-1]["content"]
                
                # Obtiene la imagen (si la hay) del último mensaje
                last_user_image_bytes = st.session_state.messages[-1].get("image")
                image_to_process = Image.open(io.BytesIO(last_user_image_bytes)) if last_user_image_bytes else None

                response_text = get_hex_response(modelo_ia, last_user_message, historial_simple, image=image_to_process)
                st.markdown(response_text)
                
                assistant_message = {"role": "assistant", "content": response_text}
                st.session_state.messages.append(assistant_message)
                # Refresca la página para mostrar la respuesta del asistente
                st.rerun()
            
            except google_exceptions.ResourceExhausted:
                st.error("⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto.")
            except Exception as e:
                st.error(f"Ha ocurrido un error inesperado: {e}")
