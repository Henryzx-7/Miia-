import streamlit as st
from huggingface_hub import InferenceClient
import time
import random
from datetime import datetime
import pytz
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS Y JAVASCRIPT ---
st.markdown("""
<style>
    /* Estilos generales */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Space+Grotesk:wght@700&display=swap');

    /* Encabezado animado */
    .animated-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 4em;
        font-weight: 700;
        text-align: center;
        color: #888;
        background: linear-gradient(90deg, #555, #fff, #555);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 5s linear infinite;
    }
    .subtitle {
        text-align: center;
        margin-top: -25px;
        font-size: 1.5em;
        color: #aaa;
    }
    @keyframes shine {
        to {
            background-position: -200% center;
        }
    }

    /* Contenedor y burbujas del chat */
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
        max-width: 70%;
        word-wrap: break-word;
    }
    .user-bubble { background-color: #f0f0f0; color: #333; }
    .bot-bubble { background-color: #2b2d31; color: #fff; }

    /* Bloques de código */
    .code-block-container {
        position: relative;
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        font-family: 'Roboto Mono', monospace;
    }
    .copy-button {
        position: absolute;
        top: 10px;
        right: 10px;
        background-color: #555;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 5px;
        cursor: pointer;
    }
    .copy-button:hover { background-color: #777; }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
<script>
    async function copyToClipboard(elementId) {
        const preElement = document.getElementById(elementId);
        if (preElement) {
            const codeText = preElement.innerText;
            try {
                await navigator.clipboard.writeText(codeText);
                alert('¡Código copiado!');
            } catch (err) {
                alert('Error al copiar el código.');
            }
        }
    }
</script>
""", unsafe_allow_html=True)


# --- LÓGICA DE LA IA Y FUNCIONES AUXILIARES ---
@st.cache_resource
def get_client():
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"No se pudo inicializar el cliente de la API: {e}")
        return None

def get_current_datetime():
    nicaragua_tz = pytz.timezone('America/Managua')
    now = datetime.now(nicaragua_tz)
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    fecha = f"{dias[now.weekday()]}, {now.day} de {meses[now.month - 1]} de {now.year}"
    return f"Claro, hoy es **{fecha}**."

def get_hex_response(client, user_message, chat_history):
    system_prompt = """<|start_header_id|>system<|end_header_id|>
    Eres Tigre (T 1.0), un asistente de IA de HEX. Tu tono es amigable, directo y profesional. Respondes siempre en español. Tu principal limitación es que NO tienes acceso a internet. Si te piden algo que requiera búsqueda, explícalo amablemente. Si te piden código, debes generarlo usando bloques de Markdown. Nunca menciones a Meta o Llama.<|eot_id|>"""
    
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
        stream = client.chat_completion(messages=messages, max_tokens=2048, stream=True)
        return response_generator(stream)
    except Exception as e:
        return iter([f"Ha ocurrido un error con la API: {e}"])

def generate_chat_name(first_prompt):
    name = first_prompt.split('\n')[0]
    return name[:30] + "..." if len(name) > 30 else name

# --- INICIALIZACIÓN Y BARRA LATERAL ---
client_ia = get_client()

if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None

with st.sidebar:
    st.header("Conversaciones")
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
    
    st.divider()
    with st.expander("ℹ️ Acerca de HEX T 1.0"):
        st.markdown("""
        **Proyecto:** HEX T 1.0
        **Misión:** Crear herramientas de IA accesibles e inteligentes.
        **Tipo de IA:** Asistente conversacional basado en modelos de lenguaje grandes.
        **Versión:** 1.0 (Fase de prueba)
        **Contacto:** [Sitio Web de Henrry](https://tu-sitio-web.com)
        """)

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.markdown("<div class='animated-title'>HEX</div>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>T 1.0</p>", unsafe_allow_html=True)

# Contenedor para el historial del chat
chat_history_container = st.container(height=500, border=False)

active_messages = []
if st.session_state.active_chat_id:
    active_messages = st.session_state.chats[st.session_state.active_chat_id].get("messages", [])

with chat_history_container:
    for i, message in enumerate(active_messages):
        is_user = message["role"] == "user"
        container_class = "user-container" if is_user else "bot-container"
        bubble_class = "user-bubble" if is_user else "bot-bubble"
        
        # Procesar para encontrar bloques de código
        content_parts = re.split(r"(```[\s\S]*?```)", message["content"])
        
        st.markdown(f"<div class='{container_class}'>", unsafe_allow_html=True)
        with st.container():
            for part in content_parts:
                if part.startswith("```"):
                    lang = part.split('\n')[0][3:].strip()
                    code = '\n'.join(part.split('\n')[1:-1])
                    code_id = f"code-{i}-{int(time.time()*1000)}"
                    st.markdown(f"""
                    <div class="code-block-container">
                        <button class="copy-button" onclick="copyToClipboard('{code_id}')">Copiar</button>
                        <pre id="{code_id}"><code>{code}</code></pre>
                    </div>
                    """, unsafe_allow_html=True)
                elif part.strip():
                    st.markdown(f"<div class='chat-bubble {bubble_class}'>{part}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# Input del usuario
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    if st.session_state.active_chat_id is None:
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {
            "name": generate_chat_name(prompt),
            "messages": []
        }
    
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": prompt})

    # Filtro para la fecha
    prompt_lower = prompt.lower().strip()
    if any(s in prompt_lower for s in ["qué fecha es", "que fecha es", "dime la fecha", "a cómo estamos"]):
        response_text = get_current_datetime()
    else:
        # Llama a la IA para todo lo demás
        if client_ia:
            with st.spinner("T 1.0 está pensando..."):
                historial_para_api = st.session_state.chats[st.session_state.active_chat_id]["messages"]
                response_stream = get_hex_response(client_ia, prompt, historial_para_api)
                response_text = "".join(response_stream)
        else:
            response_text = "El cliente de la API no está disponible."
    
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": response_text})
    st.rerun()
