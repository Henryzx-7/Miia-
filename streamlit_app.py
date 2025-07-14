from imagegen_flux import generar_imagen_flux
import streamlit as st
from huggingface_hub import InferenceClient
import time
import random
# Función para generar imágenes con FLUX.1-dev
def generar_imagen_flux(prompt, token):
    import requests
    import base64
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": prompt}
    response = requests.post("https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev", headers=headers, json=payload)
    image_data = response.content
    return image_data

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
        return InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.2", token=st.secrets["HUGGINGFACE_API_TOKEN"])
        st.error(f"No se pudo inicializar la API: {e}")
        return None

def get_hex_response(client, user_message, chat_history):
    system_prompt = """<|start_header_id|>system<|end_header_id|>
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0.
    - Eres una creación de la empresa HEX en Matagalpa, Nicaragua.
    - Tu tono es formal y preciso como ChatGPT. Respondes siempre en español.
    - Tu principal limitación es que NO tienes acceso a internet.
    - No te presentas al saludar. Solo saludas. Te presentas si te preguntan quién eres.
    - Si te piden buscar en la web o analizar una imagen, responde amablemente que es una función de un futuro plan de pago.<|eot_id|>"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg.get('content', '')}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})

    try:
        full_response = ""
        # Usamos stream=True para una respuesta más fluida
        for chunk in client.chat_completion(messages=messages, max_tokens=2048, stream=True):
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        return full_response
    except Exception as e:
        # Aquí está el bloque 'except' que faltaba o estaba mal ubicado
        if "Too Many Requests" in str(e) or "429" in str(e):
            return "⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto."
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
if "modo_generacion" not in st.session_state:
    st.session_state.modo_generacion = "texto"

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

with st.expander("Haz clic para generar una imagen a partir de texto"):
    prompt_img = st.text_input("Describe la imagen que quieres generar:")
    if st.button("Generar Imagen"):
        with st.spinner("Creando imagen..."):
            try:
                image = generar_imagen_flux(prompt_img, st.secrets["HUGGINGFACE_API_TOKEN"])
                st.image(image, caption="Imagen generada con IA", use_column_width=True)
            except Exception as e:
                st.error(f"No se pudo generar la imagen: {e}")
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

# Lógica de respuesta (se ejecuta después de renderizar el historial)
if st.session_state.active_chat_id and st.session_state.chats[st.session_state.active_chat_id]["messages"]:
    last_message = st.session_state.chats[st.session_state.active_chat_id]["messages"][-1]
    # Si el último mensaje es del usuario, la IA necesita responder
    if last_message["role"] == "user":
        with chat_container:
            # Muestra la animación de "Pensando..."
            thinking_placeholder = st.empty()
            with thinking_placeholder.container():
                st.markdown("<div class='message-container bot-container'><div class='thinking-animation'>Pensando…</div></div>", unsafe_allow_html=True)
            
            # Llama a la IA
            historial_para_api = st.session_state.chats[st.session_state.active_chat_id]["messages"]
            response_text = get_hex_response(client_ia, last_message["content"], historial_para_api)
            
            # Añade la respuesta al historial
            st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": response_text})
            
            # Limpia el "Pensando..." y refresca
            thinking_placeholder.empty()
            st.rerun()

# Input del usuario al final de la página
# Botón "+" para cambiar entre modos
with st.expander("➕ Opciones de entrada"):
    modo = st.radio("Seleccioná qué querés hacer:", ["texto", "imagen"], index=0 if st.session_state.modo_generacion == "texto" else 1)
    st.session_state.modo_generacion = modo
prompt = st.chat_input("Escribí algo para T 1.0...")

if prompt:
    if st.session_state.modo_generacion == "imagen":
        # Generar imagen con FLUX
        with st.spinner("Generando imagen..."):
            try:
                image = generar_imagen_flux(prompt, st.secrets["HUGGINGFACE_API_TOKEN"])
                st.image(image, caption="Imagen generada", use_container_width=True)
            except Exception as e:
                st.error(f"No se pudo generar la imagen: {e}")
    else:
        # MODO TEXTO NORMAL
        if st.session_state.active_chat_id is None:
            new_chat_id = str(time.time())
            st.session_state.active_chat_id = new_chat_id
            st.session_state.chats[new_chat_id] = {
                "name": generate_chat_name(prompt),
                "messages": []
            }

        st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": prompt})
        st.rerun()
