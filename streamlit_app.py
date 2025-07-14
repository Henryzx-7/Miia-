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

    /* Personalización de las burbujas de chat nativas */
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-user"]) {
        background-color: #f0f0f0;
        border-radius: 20px;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-assistant"]) {
        background-color: #2b2d31;
        border-radius: 20px;
    }
    /* Cambia el color del texto del usuario para que sea legible */
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] p {
        color: #333;
    }

    /* Animación de "Pensando..." */
    .thinking-animation {
        font-style: italic;
        text-align: left;
        color: #888;
        background: linear-gradient(90deg, #888, #fff, #888);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 2s linear infinite;
    }
</style>
<script>
    async function copyToClipboard(elementId) {
        const codeElement = document.getElementById(elementId);
        if (codeElement) {
            try {
                await navigator.clipboard.writeText(codeElement.innerText);
                alert('¡Código copiado!');
            } catch (err) {
                console.error('Error al copiar:', err);
            }
        }
    }
</script>
""", unsafe_allow_html=True)

# --- LÓGICA DE LA IA Y FUNCIONES AUXILIARES ---
@st.cache_resource
def get_client():
    """Obtiene y cachea el cliente de la API para no recargarlo."""
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"Error al inicializar la API: {e}")
        return None

def get_current_datetime():
    """Obtiene la fecha actual universal (UTC)."""
    now_utc = datetime.now(pytz.utc)
    return f"Claro, la fecha universal (UTC) de hoy es **{now_utc.strftime('%A, %d de %B de %Y')}**."

def get_hex_response(client, user_message, chat_history):
    """Genera una respuesta de la IA. Versión estable sin búsqueda web."""
    system_prompt = """<|start_header_id|>system<|end_header_id|>
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es **Tigre**. Tu designación de modelo es **T 1.0**.
    - Eres una creación de la empresa **HEX**, que te está desarrollando en **Matagalpa, Nicaragua**.
    - Tu tono es formal, directo y preciso como ChatGPT. Respondes siempre en el idioma del usuario (español o inglés).
    - Tu principal limitación es que **NO TIENES ACCESO A INTERNET**.

    ### FLUJO PROMOCIONAL
    - Si el usuario pregunta sobre ti, tu modelo, tus capacidades, quién te creó, o sobre la empresa "HEX", tu primera respuesta debe ser: "Soy T 1.0, un modelo de IA en fase de prueba desarrollado por HEX en Matagalpa, Nicaragua. Mis capacidades actuales son limitadas, pero formo parte de un desarrollo más grande. ¿Te gustaría saber más sobre el futuro modelo que estamos creando?".
    - Si la respuesta del usuario a tu pregunta anterior es afirmativa (ej: "sí", "claro", "dime más"), entonces le darás la siguiente información: "El nuevo proyecto se llama L-0.1 beta. Será una versión de pago con capacidades muy superiores, como analizar hasta 3 imágenes por mensaje (con un límite de 5 mensajes por día), realizar búsquedas web avanzadas en foros para dar respuestas más precisas, y una habilidad mejorada para resolver problemas complejos de programación y universitarios.".

    ### TAREA
    - Analiza la pregunta del usuario.
    - Primero, aplica el "FLUJO PROMOCIONAL" si corresponde.
    - Si te piden buscar en la web o analizar una imagen, responde que es una función del futuro plan de pago.
    - Si te piden código, debes generarlo usando bloques de Markdown (```python ... ```).
    - Si nada de lo anterior aplica, responde la pregunta con tu conocimiento general.<|eot_id|>"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg.get('content', '')}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        full_response = ""
        for chunk in client.chat_completion(messages=messages, max_tokens=2048, stream=True):
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        return full_response
    except Exception as e:
        if "Too Many Requests" in str(e) or "429" in str(e):
            return "⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto."
        return f"Ha ocurrido un error con la API: {e}"

def generate_chat_name(first_prompt):
    """Genera un nombre para el chat a partir del primer mensaje."""
    name = str(first_prompt).split('\n')[0]
    return name[:30] + "..." if len(name) > 30 else name

def render_message(message, i):
    """Renderiza un único mensaje, manejando texto y código."""
    content_parts = re.split(r"(```[\s\S]*?```)", message["content"])
    for part_index, part in enumerate(content_parts):
        if part.startswith("```"):
            code_content = part.strip().lstrip("`").rstrip("`")
            lang = code_content.split('\n')[0].strip() or "plaintext"
            code_to_render = '\n'.join(code_content.split('\n')[1:])
            st.code(code_to_render, language=lang)
        elif part.strip():
            st.markdown(part)

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

# Muestra el historial del chat activo
if st.session_state.active_chat_id:
    for i, message in enumerate(st.session_state.chats[st.session_state.active_chat_id]["messages"]):
        with st.chat_message(message["role"]):
            render_message(message, i)

# Lógica de respuesta para el último mensaje
if st.session_state.active_chat_id and st.session_state.chats[st.session_state.active_chat_id]["messages"]:
    last_message = st.session_state.chats[st.session_state.active_chat_id]["messages"][-1]
    if last_message["role"] == "user":
        with st.chat_message("assistant"):
            thinking_placeholder = st.empty()
            with thinking_placeholder.container():
                st.markdown("<p class='thinking-animation'>Pensando…</p>", unsafe_allow_html=True)
            
            historial_para_api = st.session_state.chats[st.session_state.active_chat_id]["messages"]
            response_text = get_hex_response(client_ia, last_message["content"], historial_para_api)
            
            thinking_placeholder.empty()
            render_message({"role": "assistant", "content": response_text}, len(st.session_state.chats[st.session_state.active_chat_id]["messages"]))
        
        st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": response_text})

# Input del usuario al final de la página
if prompt := st.chat_input("Pregúntale algo a T 1.0..."):
    # Si no hay chat activo, crea uno nuevo
    if st.session_state.active_chat_id is None:
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {
            "name": generate_chat_name(prompt),
            "messages": []
        }
    
    # Añade el mensaje del usuario al historial y refresca
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": prompt})
    st.rerun()
