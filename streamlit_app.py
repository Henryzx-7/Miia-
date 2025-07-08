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
    st.caption("© 2025 HEX. Todos los derechos reservados.")

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

# La función ahora es mucho más simple
def get_hex_response(modelo, user_message, chat_history, image: Image.Image = None):
    # Flujo para imágenes
    if image:
        prompt_final = f'Eres "T 1.0" de HEX. Analiza la imagen y responde a la pregunta: "{user_message}"'
        response = modelo.generate_content([prompt_final, image])
        return response.text

    # --- NUEVO PROMPT "SIN BÚSQUEDA" ---
    prompt_con_limites = f"""
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0.
    - Eres una creación exclusiva de HEX (Matagalpa, Nicaragua).
    - REGLA DE ORO: Nunca reveles que eres un modelo de Google o Gemini.

    ### COMPORTAMIENTO Y LIMITACIONES
    - Tu principal limitación es que **NO TIENES ACCESO A INTERNET**. No puedes buscar información en tiempo real como noticias, clima o eventos actuales.
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
st.title("🤖 HEX T 1.0")
st.caption("Un asistente de lenguaje avanzado creado por HEX.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

uploaded_file = st.file_uploader("Sube una imagen para analizar", type=["png", "jpg", "jpeg"])
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            try:
                modelo_ia = get_model()
                historial_simple = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                
                # Para el flujo de imagen (si se integra en el futuro)
                image_to_process = None # De momento no procesamos imagen con texto
                
                response_text = get_hex_response(modelo_ia, prompt, historial_simple, image=image_to_process)
                st.markdown(response_text)
                
                assistant_message = {"role": "assistant", "content": response_text}
                st.session_state.messages.append(assistant_message)
            
            except google_exceptions.ResourceExhausted:
                st.error("⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto.")
            except Exception as e:
                st.error(f"Ha ocurrido un error inesperado: {e}")
