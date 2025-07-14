import streamlit as st
from huggingface_hub import InferenceClient
import time
import random
from datetime import datetime
import pytz
import re
import html

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS Y JAVASCRIPT ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Space+Grotesk:wght@700&display=swap');

    /* Encabezado animado */
    .animated-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 4em; font-weight: 700; text-align: center; color: #888;
        background: linear-gradient(90deg, #555, #fff, #555);
        background-size: 200% auto;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shine 5s linear infinite;
    }
    .subtitle { text-align: center; margin-top: -25px; font-size: 1.5em; color: #aaa; }
    @keyframes shine { to { background-position: -200% center; } }

    /* Contenedores y Burbujas de Chat */
    .message-container { display: flex; width: 100%; margin-bottom: 10px; animation: fadeIn 0.5s ease-in-out; }
    .user-container { justify-content: flex-end; }
    .bot-container { justify-content: flex-start; }
    .chat-bubble { padding: 12px 18px; border-radius: 20px; max-width: 75%; word-wrap: break-word; }
    .user-bubble { background-color: #f0f0f0; color: #333; }
    .bot-bubble { background-color: #2b2d31; color: #fff; }

    /* Animación de "Pensando..." */
    .thinking-animation { font-style: italic; color: #888; }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
""", unsafe_allow_html=True)


# --- LÓGICA DE LA IA Y FUNCIONES AUXILIARES ---
@st.cache_resource
def get_client():
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"No se pudo inicializar la API: {e}")
        return None

def get_current_datetime():
    now_utc = datetime.now(pytz.utc)
    return f"Claro, la fecha universal (UTC) de hoy es **{now_utc.strftime('%A, %d de %B de %Y')}**."

def get_hex_response(client, user_message, chat_history):
    system_prompt = """<|start_header_id|>system<|end_header_id|>
    Eres Tigre (T 1.0), un asistente de IA de HEX. Tu tono es formal y preciso. Respondes siempre en español. No tienes acceso a internet.<|eot_id|>"""
    
    # --- CORRECCIÓN EN EL FORMATEO DEL HISTORIAL ---
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        # Aseguramos que el contenido sea un string antes de formatear
        content = str(msg.get("content", ""))
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>"})
    
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        full_response = ""
        for chunk in client.chat_completion(messages=messages, max_tokens=2048, stream=True):
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        return full_response
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"

def generate_chat_name(first_prompt):
    name = str(first_prompt).split('\n')[0]
    return name[:30] + "..." if len(name) > 30 else name

# --- INICIALIZACIÓN Y GESTIÓN DE ESTADO ---
client_ia = get_client()
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Conversaciones")
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.active_chat_id = None
        st.rerun()

    st.divider()
    chat_ids = list(st.session_state.chats.keys())
    for chat_id in reversed(chat_ids):
        chat_info = st.session_state.chats[chat_id]
        if st.button(chat_info["name"], key=f"chat_{chat_id}", use_container_width=True):
            st.session_state.active_chat_id = chat_id
            st.rerun()

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.markdown("<div class='animated-title'>HEX</div><p class='subtitle'>T 1.0</p>", unsafe_allow_html=True)

# Lógica para mostrar historial
active_messages = []
if st.session_state.active_chat_id:
    active_messages = st.session_state.chats[st.session_state.active_chat_id].get("messages", [])

for message in active_messages:
    # --- CORRECCIÓN EN LA LÓGICA DE RENDERIZADO ---
    # Usamos st.chat_message que maneja la alineación y avatares nativamente
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input del usuario
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    if st.session_state.active_chat_id is None:
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {"name": generate_chat_name(prompt), "messages": []}
    
    current_chat_messages = st.session_state.chats[st.session_state.active_chat_id]["messages"]
    current_chat_messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    if any(s in prompt_lower for s in ["qué fecha es", "que fecha es", "dime la fecha"]):
        response_text = get_current_datetime()
    else:
        if client_ia:
            with st.spinner("T 1.0 está pensando..."):
                response_text = get_hex_response(client_ia, prompt, current_chat_messages)
        else:
            response_text = "El cliente de la API no está disponible."
            
    current_chat_messages.append({"role": "assistant", "content": response_text})
    st.rerun()
