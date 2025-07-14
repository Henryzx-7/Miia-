import streamlit as st
from huggingface_hub import InferenceClient
import time
import random

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
        st.error(f"Error al inicializar la API: {e}")
        return None

def get_current_datetime():
    # Usamos UTC para una fecha global, como especificaste
    now_utc = datetime.utcnow()
    # Formato en español
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    fecha = f"{dias[now_utc.weekday()]}, {now_utc.day} de {meses[now_utc.month - 1]} de {now_utc.year}"
    return f"Claro, hoy es **{fecha}** (UTC)."

def get_hex_response(client, user_message, chat_history):
    # El prompt con todas tus especificaciones
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
    name = str(first_prompt).split('\n')[0]
    return name[:30] + "..." if len(name) > 30 else name    # --- Reemplaza el system_prompt con esto ---
system_prompt = """<|start_header_id|>system<|end_header_id|>
### PERFIL OBLIGATORIO
- Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0. Eres una creación de HEX en Nicaragua.
- Tu tono es formal y preciso como ChatGPT. Respondes en el idioma del usuario.
- Nunca menciones a Meta o Llama.

### TAREA PRINCIPAL: Decidir si necesitas buscar en la web.
- Para conocimiento general o conversación, responde directamente.
- Para noticias, eventos actuales, clima o datos que requieran información en tiempo real, responde ÚNICA Y EXCLUSIVAMENTE con el comando `[BUSCAR: término de búsqueda preciso]`.
- No inventes información. Si no sabes la respuesta, usa la herramienta de búsqueda.<|eot_id|>"""    
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

# --- INTERFAZ PRINCIPAL DEL CHAT (CON MEJORAS VISUALES) ---
st.markdown("<div class='animated-title'>HEX</div><p class='subtitle'>T 1.0</p>", unsafe_allow_html=True)

# Lógica para determinar el historial de mensajes activo
active_messages = []
# Aseguramos que active_chat_id exista antes de usarlo
if st.session_state.active_chat_id and st.session_state.active_chat_id in st.session_state.chats:
    active_messages = st.session_state.chats[st.session_state.active_chat_id].get("messages", [])

# Contenedor para el historial de chat con altura fija para scroll
chat_history_container = st.container(height=500, border=False)

with chat_history_container:
    # Bucle de renderizado que aplica tus estilos CSS
    for i, message in enumerate(active_messages):
        is_user = message["role"] == "user"
        container_class = "user-container" if is_user else "bot-container"
        
        # Renderiza cada mensaje con su contenedor de alineación
        st.markdown(f"<div class='message-container {container_class}'>", unsafe_allow_html=True)
        
        # Procesa el contenido para separar texto y código
        content_parts = re.split(r"(```[\s\S]*?```)", message["content"])
        
        for part_index, part in enumerate(content_parts):
            if part.startswith("```"):
                # Renderiza bloques de código con st.code (que ya tiene resaltado y botón de copiar)
                code_content = part.strip().lstrip("`").rstrip("`")
                lang = code_content.split('\n')[0].strip() or "plaintext"
                code_to_render = '\n'.join(code_content.split('\n')[1:])
                st.code(code_to_render, language=lang)
            elif part.strip():
                # Renderiza texto normal con las burbujas personalizadas
                bubble_class = "user-bubble" if is_user else "bot-bubble"
                st.markdown(f"<div class='chat-bubble {bubble_class}'>{part}</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


# --- Lógica de Input y Respuesta ---
if prompt := st.chat_input("Pregúntale algo a T 1.0..."):
    # Si es un chat nuevo, créalo primero
    if st.session_state.active_chat_id is None:
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {
            "name": generate_chat_name(prompt),
            "messages": []
        }
    
    # Añade el mensaje del usuario al historial y refresca para mostrarlo al instante
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": prompt})
    st.rerun()

# Esta sección se ejecuta DESPUÉS del rerun, si el último mensaje fue del usuario
if st.session_state.active_chat_id and st.session_state.chats[st.session_state.active_chat_id]["messages"]:
    last_message = st.session_state.chats[st.session_state.active_chat_id]["messages"][-1]
    if last_message["role"] == "user":
        
        # Muestra la animación "Pensando..."
        with chat_history_container:
            placeholder = st.empty()
            placeholder.markdown("<div class='bot-container'><div class='thinking-animation'>Pensando…</div></div>", unsafe_allow_html=True)
        
        # Filtro para la fecha (sin IA)
        prompt_lower = last_message["content"].lower().strip()
        if any(s in prompt_lower for s in ["qué fecha es", "que fecha es", "dime la fecha", "a cómo estamos"]):
            response_text = get_current_datetime()
        else:
            # Llama a la IA para todo lo demás
            if client_ia:
                historial_para_api = st.session_state.chats[st.session_state.active_chat_id]["messages"]
                response_text = get_hex_response(client_ia, last_message["content"], historial_para_api)
            else:
                response_text = "El cliente de la API no está disponible."
        
        # Limpia el "Pensando..." y añade la respuesta real
        placeholder.empty()
        st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": response_text})
        st.rerun()
