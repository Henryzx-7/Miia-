import streamlit as st
from huggingface_hub import InferenceClient
import time
import random
from web_tools import buscar_en_web
import re

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
    .message-container {
        display: flex;
        width: 100%;
        margin-bottom: 10px;
        animation: fadeIn 0.5s ease-in-out;
    }
    .user-container { justify-content: flex-end; }
    .bot-container { justify-content: flex-start; }
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 20px;
        max-width: 75%;
        word-wrap: break-word;
    }
    .user-bubble { background-color: #f0f0f0; color: #333; }
    .bot-bubble { background-color: #2b2d31; color: #fff; }

    /* Animación de "Pensando..." */
    .thinking-animation {
        font-style: italic;
        color: #888;
        background: linear-gradient(90deg, #666, #fff, #666);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 2s linear infinite;
        padding: 12px 18px;
        border-radius: 20px;
    }

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

# Reemplaza la función get_hex_response completa
def get_hex_response(client, user_message, chat_history, web_context=None):
    """Genera una respuesta, usando contexto web si se proporciona."""
    # Si hay contexto web, el prompt se enfoca en resumirlo
    if web_context:
        system_prompt = f"""<|start_header_id|>system<|end_header_id|>
        Eres Tigre (T 1.0), un asistente de IA de HEX. Tu tarea es responder la "Pregunta del usuario" usando la "Información de la web" que te proporciono. Actúa como si TÚ hubieras encontrado esta información. Sé conciso, profesional y responde en español.

        ### INFORMACIÓN DE LA WEB
        {web_context}
        <|eot_id|>"""
    # Si no hay contexto, es una conversación normal
    else:
        system_prompt = """<|start_header_id|>system<|end_header_id|>
        Eres Tigre, tu modelo es (T 1.0), un asistente de IA de HEX. Tu tono es amigable y profesional. Respondes en español. No tienes acceso a internet.<|eot_id|>"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})

    try:
        full_response = "".join([chunk.choices[0].delta.content for chunk in client.chat_completion(messages=messages, max_tokens=1024, stream=True) if chunk.choices[0].delta.content])
        return full_response
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg.get('content', '')}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        # Usamos stream=False para máxima estabilidad
        response = client.chat_completion(messages=messages, max_tokens=2048, stream=False)
        return response.choices[0].message.content
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
        chat_info = st.session_state.chats.get(chat_id, {})
        if st.button(chat_info.get("name", "Chat"), key=f"chat_{chat_id}", use_container_width=True):
            st.session_state.active_chat_id = chat_id
            st.rerun()

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.markdown("<div class='animated-title'>HEX</div><p class='subtitle'>T 1.0</p>", unsafe_allow_html=True)

# Contenedor para el historial de chat con altura fija
chat_container = st.container(height=450, border=False)

# Renderiza el historial de chat
if st.session_state.active_chat_id:
    active_messages = st.session_state.chats[st.session_state.active_chat_id].get("messages", [])
    with chat_container:
        for message in active_messages:
            container_class = "user-container" if message["role"] == "user" else "bot-container"
            bubble_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
            st.markdown(f"<div class='message-container {container_class}'><div class='chat-bubble {bubble_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# --- REEMPLAZA DESDE AQUÍ HASTA EL FINAL ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_message = st.session_state.messages[-1]["content"]

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            # Palabras clave que activan la búsqueda
            search_triggers = ["noticia", "actual", "hoy", "quién ganó", "cuando es", "clima"]
            prompt_lower = last_user_message.lower().strip()

            response_text = ""
            response_sources = []

            # Si el prompt contiene una palabra clave, se activa la búsqueda
            if any(trigger in prompt_lower for trigger in search_triggers):
                context, sources = buscar_en_web(last_user_message)
                # Llamamos a la IA con el contexto de la web
                response_text = get_hex_response(client_ia, last_user_message, st.session_state.messages, web_context=context)
                response_sources = sources
            else:
                # Si no, es una conversación normal sin búsqueda
                response_text = get_hex_response(client_ia, last_user_message, st.session_state.messages)

            st.markdown(response_text)
            if response_sources:
                with st.expander("Fuentes Consultadas"):
                    for source in response_sources:
                        st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")

    # Guarda la respuesta final en el historial
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "sources": response_sources
    })
    st.rerun()
