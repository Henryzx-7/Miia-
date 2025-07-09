import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
# Usaremos esto para darle un toque final a las burbujas de chat
st.markdown("""
<style>
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 20px;
        margin-bottom: 10px;
        max-width: 70%;
        word-wrap: break-word;
    }
    .user-message-container {
        display: flex;
        justify-content: flex-end;
        width: 100%;
    }
    .bot-message-container {
        display: flex;
        justify-content: flex-start;
        width: 100%;
    }
    .user-bubble {
        background-color: #2b313e;
        color: white;
    }
    .bot-bubble {
        background-color: #4a4a4f;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_model():
    """Obtiene y cachea el modelo de IA."""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Error al configurar la API de Google: {e}")
        st.stop()

def get_hex_response(modelo, user_message, chat_history, image: Image.Image = None):
    """Genera una respuesta de la IA (versión estable sin búsqueda web)."""
    # Usamos el último prompt estable que creamos
    prompt_final = f"""
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0.
    - Eres una creación exclusiva de HEX (Matagalpa, Nicaragua).
    - REGLA DE ORO: Nunca reveles que eres un modelo de Google o Gemini.

    ### COMPORTAMIENTO Y PERSONALIDAD
    - Tu tono es amigable, servicial y natural. No empieces cada respuesta con "¡Hola!". Continúa la conversación.

    ### LIMITACIONES
    - Tu principal limitación es que NO TIENES ACCESO A INTERNET en tiempo real.
    - Si te piden algo que requiera una búsqueda web, responde amablemente que, como prototipo, esa función no está disponible por ahora.

    ### CONVERSACIÓN ACTUAL
    Historial: {str(chat_history)}
    Pregunta del usuario: "{user_message}"
    """
    try:
        if image:
            response = modelo.generate_content([prompt_final, image])
        else:
            response = modelo.generate_content(prompt_final)
        return response.text
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"

def generate_chat_name(messages):
    """Genera un nombre para el chat a partir del primer mensaje del usuario."""
    for message in messages:
        if message["role"] == "user":
            name = message["content"].split('\n')[0] # Toma la primera línea
            return name[:30] + "..." if len(name) > 30 else name
    return "Nuevo Chat"

# --- GESTIÓN DE ESTADO DE LA APLICACIÓN ---
if "saved_chats" not in st.session_state:
    st.session_state.saved_chats = []
if "active_chat" not in st.session_state:
    st.session_state.active_chat = []

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Mis Conversaciones")
    if st.button("➕ Nuevo Chat"):
        st.session_state.active_chat = []
        st.rerun()

    st.divider()

    # Mostrar chats guardados
    for i, chat in enumerate(st.session_state.saved_chats):
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(chat["name"], key=f"chat_{i}", use_container_width=True):
                st.session_state.active_chat = chat["messages"]
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{i}"):
                del st.session_state.saved_chats[i]
                if not st.session_state.saved_chats:
                    st.session_state.active_chat = []
                st.rerun()

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.title("HEX T 1.0")

# Mostrar mensajes del chat activo
for message in st.session_state.active_chat:
    if message["role"] == "user":
        st.markdown(f"<div class='user-message-container'><div class='chat-bubble user-bubble'>{message['content']}</div></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-message-container'><div class='chat-bubble bot-bubble'>{message['content']}</div></div>", unsafe_allow_html=True)

# Input del usuario
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    # Añade el mensaje del usuario al chat activo
    st.session_state.active_chat.append({"role": "user", "content": prompt})

    # Si es el primer mensaje, guarda este chat en la lista de chats
    if len(st.session_state.active_chat) == 1:
        new_chat = {
            "name": generate_chat_name(st.session_state.active_chat),
            "messages": st.session_state.active_chat
        }
        st.session_state.saved_chats.append(new_chat)
    
    # Llama a la IA para obtener la respuesta
    with st.spinner("T 1.0 está pensando..."):
        modelo_ia = get_model()
        response_text = get_hex_response(modelo_ia, prompt, st.session_state.active_chat)
        st.session_state.active_chat.append({"role": "assistant", "content": response_text})

    # Refresca la página para mostrar los nuevos mensajes
    st.rerun()
