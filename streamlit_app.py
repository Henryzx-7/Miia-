import streamlit as st
from huggingface_hub import InferenceClient
import time
import random

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Space+Grotesk:wght@700&display=swap');
    /* Estilos del encabezado, burbujas de chat, etc. */
    .animated-title { font-family: 'Space Grotesk', sans-serif; font-size: 4em; font-weight: 700; text-align: center; color: #888; background: linear-gradient(90deg, #555, #fff, #555); background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: shine 5s linear infinite; }
    .subtitle { text-align: center; margin-top: -25px; font-size: 1.5em; color: #aaa; }
    @keyframes shine { to { background-position: -200% center; } }
    .message-container { display: flex; width: 100%; margin-bottom: 10px; animation: fadeIn 0.5s ease-in-out; }
    .user-container { justify-content: flex-end; }
    .bot-container { justify-content: flex-start; }
    .chat-bubble { padding: 12px 18px; border-radius: 20px; max-width: 75%; word-wrap: break-word; }
    .user-bubble { background-color: #f0f0f0; color: #333; }
    .bot-bubble { background-color: #2b2d31; color: #fff; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_client():
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"Error al inicializar la API: {e}")
        return None

def get_hex_response(client, user_message, chat_history):

    system_prompt = """<|start_header_id|>system<|end_header_id|>
    Eres Tigre, usas el modelo T 1.0, un asistente de IA conversacional de la empresa HEX. Tu tono es amigable y profesional.
    - Responde siempre en el mismo idioma que el usuario.
    - Tu conocimiento es general y no tienes acceso a internet para eventos en tiempo real.
    - Si te preguntan por tus capacidades, puedes mencionar que ayudas a generar ideas, explicar temas y conversar.
    - Nunca menciones que eres un modelo de Meta o Llama.<|eot_id|>"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        # Usamos st.write_stream para una respuesta fluida
        response_stream = client.chat_completion(messages=messages, max_tokens=1024, stream=True)
        return response_stream
    except Exception as e:
        if "Too Many Requests" in str(e) or "429" in str(e):
            return iter(["⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto."])
        return iter([f"Ha ocurrido un error con la API: {e}"])

def generate_chat_name(first_prompt):
    name = first_prompt.split('\n')[0]
    return name[:30] + "..." if len(name) > 30 else name

# --- INICIALIZACIÓN Y GESTIÓN DE ESTADO ---
client_ia = get_client()

if "chats" not in st.session_state:
    st.session_state.chats = {}
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

# --- INTERFAZ PRINCIPAL ---
st.markdown("<div class='animated-title'>HEX</div><p class='subtitle'>T 1.0</p>", unsafe_allow_html=True)

# Define el chat activo
active_chat = None
if st.session_state.active_chat_id:
    active_chat = st.session_state.chats[st.session_state.active_chat_id]
else:
    # Si no hay chat activo, muestra un mensaje de bienvenida
    st.info("Selecciona un chat o inicia uno nuevo para comenzar.")

# Muestra el historial del chat activo
if active_chat:
    for message in active_chat["messages"]:
        container_class = "user-container" if message["role"] == "user" else "bot-container"
        bubble_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
        st.markdown(f"<div class='message-container {container_class}'><div class='chat-bubble {bubble_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# Input del usuario
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    # Si no hay un chat activo, crea uno nuevo
    if st.session_state.active_chat_id is None:
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {
            "name": generate_chat_name(prompt),
            "messages": []
        }
    
    # Añade el mensaje del usuario al historial activo
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": prompt})
    
    # Llama a la IA para obtener la respuesta
    if client_ia:
        with st.spinner("T 1.0 está pensando..."):
            historial_para_api = st.session_state.chats[st.session_state.active_chat_id]["messages"]
            response_stream = get_hex_response(client_ia, prompt, historial_para_api)
            
            # Usamos st.write_stream para la animación de escritura
            response_text = st.write_stream(response_stream)
            st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": response_text})
    else:
        response_text = "El cliente de la API no está disponible."
        st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": response_text})

    st.rerun()
