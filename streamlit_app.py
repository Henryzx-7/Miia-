import streamlit as st
import time
from huggingface_hub import InferenceClient

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 20px;
        margin-bottom: 10px;
        max-width: 70%;
        word-wrap: break-word;
        clear: both;
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
        background-color: #0b93f6;
        color: white;
    }
    .bot-bubble {
        background-color: #e5e5ea;
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
client_ia = get_client()

# Inicialización del estado de la sesión
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None

# --- BARRA LATERAL (SIDEBAR) PARA GESTIÓN DE CHATS ---
with st.sidebar:
    st.header("Mis Conversaciones")
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.active_chat_id = None
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

# --- ÁREA PRINCIPAL DEL CHAT ---
st.title("HEX T 1.0")

if st.session_state.active_chat_id is None and len(st.session_state.chats) > 0:
    # Si no hay chat activo pero hay chats guardados, activa el más reciente
    st.session_state.active_chat_id = list(st.session_state.chats.keys())[-1]

active_messages = st.session_state.chats.get(st.session_state.active_chat_id, {}).get("messages", [])

# Muestra el historial de chat activo
for message in active_messages:
    st.markdown(f"<div class='{message['role']}-container'><div class='chat-bubble {message['role']}-bubble'>{message['content']}</div></div>", unsafe_allow_html=True)

# Input del usuario
if prompt := st.chat_input("Pregúntale algo a T 1.0..."):
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
        with st.chat_message("assistant"): # Placeholder para el spinner
            with st.spinner("T 1.0 está pensando..."):
                # --- CORRECCIÓN CLAVE ---
                # Pasamos la lista de mensajes, no el diccionario de chat completo
                response_stream = get_hex_response(
                    client_ia,
                    prompt, 
                    st.session_state.chats[st.session_state.active_chat_id]["messages"]
                )
                bot_response = st.write_stream(response_stream)
        st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": bot_response})
    else:
        st.error("El cliente de la API no está disponible.")
    
    st.rerun()
