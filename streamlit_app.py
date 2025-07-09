import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image
import io
import time
import random

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    /* Elimina el espacio extra en la parte superior */
    .block-container {
        padding-top: 2rem;
    }
    /* Contenedor de la burbuja de chat */
    .chat-bubble {
        display: inline-block;
        padding: 10px 15px;
        border-radius: 20px;
        margin-bottom: 10px;
        max-width: 75%;
        word-wrap: break-word;
    }
    /* Contenedor para alinear los mensajes */
    .message-container {
        display: flex;
        width: 100%;
        margin-bottom: 5px;
    }
    /* Mensajes del usuario (derecha) */
    .user-container {
        justify-content: flex-end;
    }
    /* Mensajes del bot (izquierda) */
    .bot-container {
        justify-content: flex-start;
    }
    .user-bubble {
        background-color: #0b93f6; /* Azul para el usuario */
        color: white;
    }
    .bot-bubble {
        background-color: #e5e5ea; /* Gris claro para el bot */
        color: black;
    }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_client():
    """Obtiene y cachea el cliente de la API para no recargarlo."""
    try:
        client = InferenceClient(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            token=st.secrets["HUGGINGFACE_API_TOKEN"]
        )
        return client
    except Exception as e:
        st.error(f"No se pudo inicializar el cliente de la API: {e}")
        return None

def get_hex_response(client, user_message, chat_history):
    """Genera una respuesta de la IA."""
    system_prompt = """<|start_header_id|>system<|end_header_id|>
    Eres Tigre (T 1.0), un asistente de IA de la empresa HEX. Tu tono es amigable, directo y profesional. Respondes siempre en el idioma del usuario. Tu principal limitación es que NO tienes acceso a internet. Si te piden algo que requiera búsqueda (noticias, clima), explícalo amablemente. Nunca menciones a Meta o Llama.<|eot_id|>"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        # Ya no usamos streaming para máxima estabilidad
        response = client.chat_completion(messages=messages, max_tokens=1024, stream=False)
        return response.choices[0].message.content
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"

def generate_chat_name(first_prompt):
    """Genera un nombre para el chat a partir del primer mensaje."""
    name = first_prompt.split('\n')[0]
    return name[:30] + "..." if len(name) > 30 else name

# --- INICIALIZACIÓN ---
client_ia = get_client()

if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if not st.session_state.active_chat_id and st.session_state.chats:
    st.session_state.active_chat_id = list(st.session_state.chats.keys())[-1]

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Mis Conversaciones")
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.active_chat_id = None
        st.session_state.messages = [] # Limpiamos los mensajes activos
        st.rerun()

    st.divider()
    chat_ids = list(st.session_state.chats.keys())
    for chat_id in reversed(chat_ids):
        chat_info = st.session_state.chats[chat_id]
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(chat_info["name"], key=f"chat_{chat_id}", use_container_width=True):
                st.session_state.active_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}"):
                del st.session_state.chats[chat_id]
                if st.session_state.active_chat_id == chat_id:
                    st.session_state.active_chat_id = None
                st.rerun()

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.title("HEX T 1.0")

# Contenedor para el historial del chat
chat_history_container = st.container(height=500, border=False)

with chat_history_container:
    if st.session_state.active_chat_id:
        active_messages = st.session_state.chats[st.session_state.active_chat_id].get("messages", [])
        for message in active_messages:
            container_class = "user-container" if message["role"] == "user" else "bot-container"
            bubble_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
            st.markdown(f"<div class='message-container {container_class}'><div class='chat-bubble {bubble_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# Input del usuario
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    # Si es un chat nuevo, créalo
    if st.session_state.active_chat_id is None:
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {
            "name": generate_chat_name(prompt),
            "messages": []
        }

    # Añade el mensaje del usuario al historial activo
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": prompt})

    # Llama a la IA y guarda su respuesta
    if client_ia:
        with st.spinner("T 1.0 está pensando..."):
            historial_para_api = st.session_state.chats[st.session_state.active_chat_id]
            response_text = get_hex_response(client_ia, prompt, historial_para_api["messages"])
            st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": response_text})
    else:
        st.error("El cliente de la API no está disponible.")
    
    st.rerun()
