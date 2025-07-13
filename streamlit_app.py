import streamlit as st
import time
from huggingface_hub import InferenceClient

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    /* Estilo para las burbujas de chat */
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 20px;
        margin-bottom: 10px;
        max-width: 75%;
        word-wrap: break-word;
        clear: both;
    }
    .user-bubble {
        float: right;
        background-color: #0b93f6; /* Azul para el usuario */
        color: white;
    }
    .bot-bubble {
        float: left;
        background-color: #2b2d31; /* Gris oscuro para el bot */
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_client():
    """Obtiene y cachea el cliente de la API para no recargarlo."""
    try:
        return InferenceClient(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            token=st.secrets["HUGGINGFACE_API_TOKEN"]
        )
    except Exception as e:
        st.error(f"Error al inicializar la API: {e}")
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
        # Usamos chat_completion que es el método correcto
        full_response = ""
        for chunk in client.chat_completion(messages=messages, max_tokens=1024, stream=True):
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        return full_response
    except Exception as e:
        # Manejo de error de límite de uso
        if "Too Many Requests" in str(e) or "429" in str(e):
            return "⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto."
        return f"Ha ocurrido un error con la API: {e}"

def generate_chat_name(first_prompt):
    """Genera un nombre para el chat a partir del primer mensaje."""
    name = first_prompt.split('\n')[0]
    return name[:30] + "..." if len(name) > 30 else name

# --- INICIALIZACIÓN Y GESTIÓN DE ESTADO ---
client_ia = get_client()

if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = "new_chat"
    st.session_state.chats["new_chat"] = {"name": "Nuevo Chat", "messages": []}

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Mis Conversaciones")
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.active_chat_id = "new_chat"
        st.session_state.chats["new_chat"] = {"name": "Nuevo Chat", "messages": []}
        st.rerun()

    st.divider()
    chat_ids = list(st.session_state.chats.keys())
    for chat_id in reversed(chat_ids):
        if chat_id == "new_chat": continue
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
                    st.session_state.active_chat_id = "new_chat"
                st.rerun()

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.title("HEX T 1.0")

# Contenedor para el historial del chat
chat_history_container = st.container(height=400, border=False)

active_messages = st.session_state.chats[st.session_state.active_chat_id].get("messages", [])

with chat_history_container:
    for message in active_messages:
        # Usa el diseño de burbujas con CSS y float
        bubble_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
        st.markdown(f"<div class='message-container'><div class='chat-bubble {bubble_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# Input del usuario
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    active_chat_id = st.session_state.active_chat_id
    # Si es un chat nuevo, se crea aquí
    if active_chat_id == "new_chat":
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {
            "name": generate_chat_name(prompt),
            "messages": []
        }
        del st.session_state.chats["new_chat"]
    
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": prompt})

    # Lógica de respuesta de la IA
    if client_ia:
        with st.spinner("T 1.0 está pensando..."):
            historial_para_api = st.session_state.chats[st.session_state.active_chat_id]["messages"]
            response_text = get_hex_response(client_ia, prompt, historial_para_api)
            st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": response_text})
    else:
        st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": "El cliente de la API no está disponible."})
    
    st.rerun()
