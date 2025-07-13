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
    /* ... (Todos tus estilos CSS van aquí sin cambios) ... */
    .user-bubble { background-color: #f0f0f0; color: #333; float: right; }
    .bot-bubble { background-color: #2b2d31; color: #fff; float: left; }
    /* etc. */
</style>
""", unsafe_allow_html=True) # El CSS completo que ya tenías

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_client():
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"Error al inicializar la API: {e}")
        return None

# Eliminamos el caché de esta función porque el historial dinámico lo hace complejo
def get_hex_response(client, user_message, chat_history):
    # El prompt se mantiene igual
    system_prompt = """<|start_header_id|>system<|end_header_id|>
    Eres Tigre (T 1.0)... (el resto de tu prompt va aquí) <|eot_id|>"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        full_response = "".join([chunk.choices[0].delta.content for chunk in client.chat_completion(messages=messages, max_tokens=2048, stream=True) if chunk.choices[0].delta.content])
        return full_response
    except Exception as e:
        if "Too Many Requests" in str(e) or "429" in str(e):
            return "⚠️ Límite de solicitudes alcanzado."
        return f"Ha ocurrido un error con la API: {e}"

def generate_chat_name(first_prompt):
    name = first_prompt.split('\n')[0]
    return name[:30] + "..." if len(name) > 30 else name

# --- INICIALIZACIÓN Y GESTIÓN DE ESTADO ---
client_ia = get_client()
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = "new_chat"
    st.session_state.chats["new_chat"] = {"name": "Nuevo Chat", "messages": []}

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Conversaciones")
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.active_chat_id = "new_chat"
        st.session_state.chats["new_chat"] = {"name": "Nuevo Chat", "messages": []}
        st.rerun()
    # ... (resto del código del sidebar que ya tenías)

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.markdown("<div class='animated-title'>HEX</div><p class='subtitle'>T 1.0</p>", unsafe_allow_html=True)

# Define el chat activo
active_messages = st.session_state.chats.get(st.session_state.active_chat_id, {}).get("messages", [])

# Renderiza el historial
for message in active_messages:
    # ... (resto del código para renderizar burbujas que ya tenías)
    pass

# --- LÓGICA DE INPUT Y RESPUESTA (REFACTORIZADA) ---
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    active_chat_id = st.session_state.active_chat_id
    if active_chat_id == "new_chat":
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = { "name": generate_chat_name(prompt), "messages": [] }
        if "new_chat" in st.session_state.chats:
             del st.session_state.chats["new_chat"]

    current_chat = st.session_state.chats[st.session_state.active_chat_id]
    current_chat["messages"].append({"role": "user", "content": prompt})

    if client_ia:
        with st.spinner("T 1.0 está pensando..."):
            response_text = get_hex_response(client_ia, prompt, current_chat["messages"])
            current_chat["messages"].append({"role": "assistant", "content": response_text})
    else:
        current_chat["messages"].append({"role": "assistant", "content": "El cliente de la API no está disponible."})
    
    st.rerun()
