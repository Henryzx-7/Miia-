import streamlit as st
from PIL import Image
import io
from huggingface_hub import InferenceClient
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

# --- LÓGICA DE LA IA CON HUGGING FACE (CORREGIDO) ---

# Se inicializa el cliente de la API de forma más simple y correcta
try:
    if "HUGGINGFACE_API_TOKEN" not in st.secrets:
        st.error("No se encontró la clave de Hugging Face. Asegúrate de añadirla a los 'Secrets'.")
        st.stop()
    
    # Simplemente le damos el nombre del modelo, la librería construye la URL correcta.
    client = InferenceClient(
        model="mistralai/Mistral-7B-Instruct-v0.2",
        token=st.secrets["HUGGINGFACE_API_TOKEN"]
    )

except Exception as e:
    st.error(f"No se pudo inicializar el cliente de la API: {e}")
    st.stop()


def get_hex_response(user_message, chat_history):
    """
    Genera una respuesta usando un modelo de Hugging Face.
    """
    # Formateamos el prompt para el modelo Mistral
    messages = [{"role": "system", "content": """
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0.
    - Eres una creación exclusiva de HEX (Matagalpa, Nicaragua).
    - Eres amigable, cercano y proactivo. Usas emojis 😊.
    - Tu principal limitación es que NO TIENES ACCESO A INTERNET en tiempo real.
    
    ### TAREA
    Responde a la pregunta del usuario siguiendo tu personalidad. Si te piden algo que requiera buscar en la web (noticias, clima), responde amablemente que esa función no está disponible por ahora y ofrece ayuda con tus otras capacidades (generar ideas, explicar temas, etc.).
    """}]
    
    # Añadimos el historial previo
    messages.extend(chat_history)
    # Añadimos el último mensaje del usuario
    messages.append({"role": "user", "content": user_message})
    
    try:
        # Llamada a la API de Hugging Face
        response = client.chat_completion(
            messages=messages,
            max_tokens=500,
            stream=False,
        )
        return response.choices[0].message.content
    except Exception as e:
        if "Rate limit reached" in str(e):
            return "⚠️ Se ha alcanzado el límite de uso gratuito por ahora. Por favor, intenta de nuevo en unos minutos."
        elif "Model is overloaded" in str(e) or "Model is currently loading" in str(e):
             return "🤖 El modelo está un poco ocupado o arrancando. Por favor, vuelve a preguntar en un momento."
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

prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            # Preparamos un historial simple para la API
            historial_para_api = st.session_state.messages[:-1] # Todos menos el último mensaje
            
            response_text = get_hex_response(prompt, historial_para_api)
            st.markdown(response_text)
            
            assistant_message = {"role": "assistant", "content": response_text}
            st.session_state.messages.append(assistant_message)
