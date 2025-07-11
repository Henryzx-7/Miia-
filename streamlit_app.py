import streamlit as st
from huggingface_hub import InferenceClient
import time
import random
from datetime import datetime
import pytz
import re
import html
from PIL import Image

# --- BLOQUE DE AUTENTICACIÓN ---

# Base de datos de usuarios en memoria (en un caso real, esto vendría de una base de datos)
# La contraseña debe ser guardada usando un hash, pero para este ejemplo es texto plano.
VALID_USERS = {
    "henrry": "12345",
    "invitado": "invitado"
}

def check_login():
    """Muestra el formulario de login y verifica las credenciales."""
    st.set_page_config(page_title="Inicio de Sesión - HEX T 1.0", layout="centered")
    st.header("Inicio de Sesión")
    
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar", use_container_width=True):
        # Verifica las credenciales
        if username in VALID_USERS and password == VALID_USERS[username]:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun() # Vuelve a ejecutar el script para mostrar la app principal
        else:
            st.error("Usuario o contraseña incorrectos.")
            
# --- FIN DEL BLOQUE DE AUTENTICACIÓN ---

# --- ESTRUCTURA PRINCIPAL DE LA APP ---

# Inicializa el estado de autenticación
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Muestra el login o la app principal
if not st.session_state.authenticated:
    check_login()
else:
    # --- TODO TU CÓDIGO ANTERIOR VA AQUÍ DENTRO ---
    # (Desde st.set_page_config hasta el final)
    
    # Ejemplo de cómo se vería el inicio:
    st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")
    
    # Saludo personalizado
    st.sidebar.success(f"Sesión iniciada como: **{st.session_state.username}**")
    
    # ... y aquí sigue todo el resto del código que ya tenías
    # (CSS, Lógica de la IA, Interfaz del Chat, etc.)
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

    /* --- NUEVA LÓGICA DE BURBUJAS DE CHAT CON 'FLOAT' --- */
    .message-container {
        width: 100%;
        overflow: auto; /* 'Clearfix' para que los floats no se sobrepongan */
        margin-bottom: 10px;
        animation: fadeIn 0.5s ease-in-out;
    }
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 20px;
        max-width: 75%;
        word-wrap: break-word;
    }
    .user-bubble {
        float: right; /* Fuerza el elemento a alinearse a la derecha */
        background-color: #f0f0f0;
        color: #333;
    }
    .bot-bubble {
        float: left; /* Fuerza el elemento a alinearse a la izquierda */
        background-color: #2b2d31;
        color: #fff;
    }
    
    /* El resto de los estilos se mantienen igual */
    .thinking-animation-container { display: flex; justify-content: flex-start; width: 100%; margin: 10px 0; }
    .thinking-animation {
        font-style: italic; color: #888;
        background: linear-gradient(90deg, #666, #fff, #666);
        background-size: 200% auto;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shine 2s linear infinite;
        padding: 12px 18px; border-radius: 20px;
        background-color: #2b2d31;
    }
    .code-block-container { position: relative; background-color: #1e1e1e; border-radius: 8px; margin: 1rem 0; color: #f0f0f0; }
    .code-block-header { display: flex; justify-content: space-between; align-items: center; background-color: #333; padding: 8px 12px; border-top-left-radius: 8px; border-top-right-radius: 8px;}
    .code-block-lang { color: #ccc; font-size: 0.9em; font-family: 'Roboto Mono', monospace; }
    .copy-button { background-color: #555; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; font-size: 0.8em; }
    .copy-button:hover { background-color: #777; }
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
<script>
    async function copyToClipboard(elementId) {
        const codeElement = document.getElementById(elementId);
        if (codeElement) {
            try {
                await navigator.clipboard.writeText(codeElement.innerText);
                alert('¡Código copiado!');
            } catch (err) {
                alert('Error al copiar.');
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
        st.error(f"No se pudo inicializar la API: {e}")
        return None

def get_current_datetime():
    now_utc = datetime.utcnow()
    return f"Claro, la fecha universal (UTC) de hoy es **{now_utc.strftime('%A, %d de %B de %Y')}**."

def get_hex_response(client, user_message, chat_history):
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
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        full_response = "".join([chunk.choices[0].delta.content for chunk in client.chat_completion(messages=messages, max_tokens=2048, stream=True) if chunk.choices[0].delta.content])
        return full_response
    except Exception as e:
        if "Too Many Requests" in str(e) or "429" in str(e):
            return "⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto."
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
    
    st.divider()
    with st.expander("ℹ️ Acerca de HEX T 1.0"):
        st.markdown("**Proyecto:** HEX T 1.0 ...")

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.markdown("<div class='animated-title'>HEX</div><p class='subtitle'>T 1.0</p>", unsafe_allow_html=True)

# -- BLOQUE DE CÓDIGO AÑADIDO --
# Determina qué historial de mensajes mostrar
active_messages = []
if st.session_state.active_chat_id and st.session_state.active_chat_id in st.session_state.chats:
    active_messages = st.session_state.chats[st.session_state.active_chat_id].get("messages", [])

# Renderiza el historial de chat con la nueva lógica
for i, message in enumerate(active_messages):
    container_class = "user-container" if message["role"] == "user" else "bot-container"
    st.markdown(f"<div class='{container_class}'>", unsafe_allow_html=True)
    
    content_parts = re.split(r"(```[\s\S]*?```)", message["content"])
    
    for part_index, part in enumerate(content_parts):
        if part.startswith("```"):
            code_content = part.strip().lstrip("`").rstrip("`")
            lang = code_content.split('\n')[0].strip() or "plaintext"
            code = '\n'.join(code_content.split('\n')[1:])
            st.code(code, language=lang) # Usamos st.code() para el renderizado nativo
        elif part.strip():
            bubble_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
            st.markdown(f"<div class='chat-bubble {bubble_class}'>{part}</div>", unsafe_allow_html=True)
            
    st.markdown("</div>", unsafe_allow_html=True)


# --- REEMPLAZA DESDE AQUÍ HASTA EL FINAL DEL 

# --- REEMPLAZA DESDE AQUÍ HASTA EL FINAL DEL ARCHIVO ---

# Input del usuario
uploaded_file = st.file_uploader("Sube una imagen para analizar", type=["png", "jpg", "jpeg"])
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt or uploaded_file:
    # --- LÓGICA UNIFICADA PARA MANEJAR TEXTO E IMÁGENES ---
    
    # Determina el contenido del mensaje del usuario
    user_input_content = prompt or "Analiza la imagen que he subido."
    
    # Si es un chat nuevo, se crea aquí
    if st.session_state.active_chat_id is None:
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {
            "name": generate_chat_name(user_input_content),
            "messages": []
        }
    
    # Añade el mensaje del usuario al historial
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": user_input_content})
    
    # Prepara la imagen si existe
    image_to_process = None
    if uploaded_file:
        try:
            image_to_process = Image.open(uploaded_file)
        except Exception as e:
            st.error(f"No se pudo abrir la imagen: {e}")
            image_to_process = None

    # Lógica de respuesta
    prompt_lower = (prompt or "").lower().strip()
    if any(s in prompt_lower for s in ["qué fecha es", "que fecha es", "dime la fecha", "a cómo estamos"]):
        response_text = get_current_datetime()
    else:
        if client_ia:
            with st.spinner("T 1.0 está pensando..."):
                historial_para_api = st.session_state.chats[st.session_state.active_chat_id]["messages"]
                
                # Llamamos a la IA con el texto y la imagen (si existe)
                response_text = get_hex_response(client_ia, user_input_content, historial_para_api, image=image_to_process)
        else:
            response_text = "El cliente de la API no está disponible."
    
    # Añade la respuesta de la IA al historial
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": response_text})
    st.rerun()
