import streamlit as st
from huggingface_hub import InferenceClient
import time
import random

# --- CONFIGURACIÓN DE LA PÁGINA Y ESTILOS ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# CSS para el diseño de las burbujas de chat estilo ChatGPT
st.markdown("""
<style>
    .chat-container {
        display: flex;
        flex-direction: column;
    }
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 20px;
        margin-bottom: 10px;
        max-width: 70%;
        word-wrap: break-word;
    }
    .user-container {
        display: flex;
        justify-content: flex-end;
        width: 100%;
    }
    .bot-container {
        display: flex;
        justify-content: flex-start;
        width: 100%;
    }
    .user-bubble {
        background-color: #0b93f6; /* Azul claro para el usuario */
        color: white;
    }
    .bot-bubble {
        background-color: #e5e5ea; /* Gris claro para el bot */
        color: black;
    }
</style>
""", unsafe_allow_html=True)


# --- LÓGICA DE LA IA Y FUNCIONES AUXILIARES ---
@st.cache_resource
def get_model():
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
    """Genera una respuesta de la IA (versión estable sin búsqueda web)."""
    system_prompt = """<|start_header_id|>system<|end_header_id|>
    Eres Tigre (T 1.0), un asistente de IA de HEX. Tu tono es amigable, directo y profesional. Respondes siempre en el idioma del usuario. Tu principal limitación es que NO tienes acceso a internet. Si te piden algo que requiera búsqueda (noticias, clima), explícalo amablemente. Nunca menciones a Meta o Llama.<|eot_id|>"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    def response_generator(stream):
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    try:
        stream = client.chat_completion(messages=messages, max_tokens=1024, stream=True)
        return response_generator(stream)
    except Exception as e:
        return iter([f"Ha ocurrido un error con la API: {e}"])

def generate_chat_name(first_prompt):
    """Genera un nombre para el chat a partir del primer mensaje."""
    name = first_prompt.split('\n')[0]
    return name[:30] + "..." if len(name) > 30 else name

# --- GESTIÓN DE ESTADO E INTERFAZ ---
modelo_ia = get_model()

# Inicialización del estado de la sesión
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None

# --- BARRA LATERAL (SIDEBAR) PARA GESTIÓN DE CHATS ---
with st.sidebar:
    st.header("Historial de Chats")
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.active_chat_id = None
        st.rerun()

    st.divider()

    # Mostrar chats guardados con opción para eliminar
    chat_ids = list(st.session_state.chats.keys())
    for chat_id in reversed(chat_ids): # Mostrar los más recientes primero
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

# --- ÁREA PRINCIPAL DEL CHAT ---
st.title("HEX T 1.0")

# Determina qué historial de mensajes mostrar
if st.session_state.active_chat_id is None:
    active_messages = []
else:
    active_messages = st.session_state.chats[st.session_state.active_chat_id]["messages"]

# Muestra el historial de chat activo con el nuevo diseño
for message in active_messages:
    if message["role"] == "user":
        st.markdown(f"<div class='user-message-container'><div class='chat-bubble user-bubble'>{message['content']}</div></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-message-container'><div class='chat-bubble bot-bubble'>{message['content']}</div></div>", unsafe_allow_html=True)

# Input del usuario
if prompt := st.chat_input("Pregúntale algo a T 1.0..."):
    # Si es un chat nuevo, créalo y asígnale un ID
    if st.session_state.active_chat_id is None:
        new_chat_id = str(time.time()) # Usamos timestamp como ID único
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {
            "name": generate_chat_name(prompt),
            "messages": []
        }

    # Añade el mensaje del usuario al historial activo
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": prompt})

    # Llama a la IA y guarda su respuesta
    with st.spinner("T 1.0 está pensando..."):
        response_stream = get_hex_response(prompt, st.session_state.chats[st.session_state.active_chat_id])
        # Usamos st.write_stream para mostrar la respuesta palabra por palabra
        bot_response = st.write_stream(response_stream)
        st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": bot_response})
    
    st.rerun()
