import streamlit as st
from huggingface_hub import InferenceClient
import time
import random
from PIL import Image
import requests, base64, io

def generar_imagen_flux(prompt, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": prompt}  # 👈 aquí está el cambio importante
    response = requests.post(
        "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev",
        headers=headers,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(f"Error en la API: {response.status_code} - {response.text}")
    
    image = Image.open(io.BytesIO(response.content))
    return image

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
    .chat-row {
        display: flex;
        align-items: center;
    }
    .plus-button {
        font-size: 1.5em;
        margin-left: 10px;
        cursor: pointer;
    }
    .modo-popup {
        background-color: #2b2d31;
        padding: 10px;
        border-radius: 10px;
        margin-top: -80px;
        position: absolute;
        right: 100px;
        z-index: 9999;
    }
    .modo-popup label {
        color: white;
        font-size: 0.9em;
        display: block;
        margin-bottom: 5px;
        cursor: pointer;
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

def get_hex_response(client, user_message, chat_history):
    system_prompt = """<|start_header_id|>system<|end_header_id|>
    tu nombre legitimo es Tigre, Tu modelo es T 1.0, un asistente de IA de HEX. Tu tono es amigable, directo y profesional. Respondes siempre en el idioma del usuario. Tu principal limitación es que NO tienes acceso a internet. Si te piden algo que requiera búsqueda (noticias, clima), explícalo amablemente. Nunca menciones a Meta o Llama, puedes programar medianamete como Varias IA, siempre que te hagan preguntas sobre la empresa que te creo (HEX) di que son de nicaragua y que haran un futuro modelo hermano tuyo llamado L 0.1 preview y tendran mas ventajas y sera accecibles para todos pero con limitaciones, La empresa que te creo se llama HEX y es de Nicaragua, Matagalpa, fuiste creado por expertos, Presentate una sola vez almenos que te pregunten de nuevo, ahora tienes la funcion de crear imagenes pero no por ti sola te pueden activa con la cruz que esta abajo de la barra de chat y seleccionar la que dice genera imagen, presentare una vez y no hablez de quien te creo almenos que te pregunten.<|eot_id|>"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg.get('content', '')}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        # Usamos stream=False para máxima estabilidad
        time.sleep(2)
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

            if "image_bytes" in message:
                st.markdown(f"<div class='message-container {container_class}'><div class='chat-bubble {bubble_class}'>{message['content']}</div></div>", unsafe_allow_html=True)
                st.image(io.BytesIO(message["image_bytes"]), use_container_width=True)
            else:
                st.markdown(f"<div class='message-container {container_class}'><div class='chat-bubble {bubble_class}'>{message['content']}</div></div>", unsafe_allow_html=True)
# Lógica de respuesta (se ejecuta después de renderizar el historial)
if st.session_state.active_chat_id and st.session_state.chats[st.session_state.active_chat_id]["messages"]:
    last_message = st.session_state.chats[st.session_state.active_chat_id]["messages"][-1]
    # Si el último mensaje es del usuario, la IA necesita responder
    if last_message["role"] == "user" and st.session_state.modo_generacion == "texto":
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
            # Inicializa el modo si no existe
if "modo_generacion" not in st.session_state:
    st.session_state.modo_generacion = "texto"
if "mostrar_selector" not in st.session_state:
    st.session_state.mostrar_selector = False
if "modo_ocr" not in st.session_state:
    st.session_state.modo_ocr = False
if "imagen_cargada" not in st.session_state:
    st.session_state.imagen_cargada = None
if "texto_adicional" not in st.session_state:
    st.session_state.texto_adicional = ""

# Input del usuario al final de la página
# Input del usuario al final de la página
with st.container():
    col1, col2 = st.columns([10, 1])

    with col1:
        if st.session_state.get("bloqueado", False):
            prompt = None
            st.chat_input("Procesando imagen... espera un momento.", disabled=True)
        else:
            prompt = st.chat_input("Escríbele lo que quieras...", key="chat_input")

    with col2:
        if st.button("➕", key="plus_button", help="Cambiar modo o subir imagen", disabled=st.session_state.get("bloqueado", False)):
            st.session_state.mostrar_selector = not st.session_state.mostrar_selector

        imagen_cargada = st.file_uploader(
            "📷➕",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed",
            key="upload_imagen"
        )

        if imagen_cargada:
            st.session_state.imagen_cargada = imagen_cargada
            st.session_state.modo_ocr = True
            st.toast("Imagen cargada. Escribe un mensaje si deseas y presiona Enter para enviarla.", icon="📷")

# Selector flotante de modo
# Selector flotante de modo (usando st.radio en lugar de HTML)
if st.session_state.mostrar_selector:
    with st.container():
        modo_humano = st.radio(
            "Selecciona el modo:",
            ["¡Habla con Tigre!", "Generar imágenes"],
            index=0 if st.session_state.modo_generacion == "texto" else 1,
            key="modo_radio",
            label_visibility="collapsed"
        )
        # 👇 Solo se ejecuta si se muestra el selector
        st.session_state.modo_generacion = "texto" if modo_humano == "¡Habla con Tigre!" else "imagen"
# Detectar el modo desde URL temporal
# (Ya no es necesario usar query_params porque usamos st.radio)
pass  # Eliminamos esta parte

# 👇 Este bloque es independiente y solo se ejecuta si el usuario escribió algo
# 👇 Este bloque es independiente y solo se ejecuta si el usuario escribió algo
if prompt:
    # 👇 Si hay imagen pendiente, procesamos OCR en vez de texto
    if st.session_state.modo_ocr and st.session_state.imagen_cargada:
        texto = prompt  # Guardamos lo que escribió el usuario
        imagen = st.session_state.imagen_cargada
        st.session_state.imagen_cargada = None
        st.session_state.modo_ocr = False
        st.session_state.uploader_key += 1

        # Creamos chat si no existe
        if st.session_state.active_chat_id is None:
            new_chat_id = str(time.time())
            st.session_state.active_chat_id = new_chat_id
            st.session_state.chats[new_chat_id] = {
                "name": generate_chat_name(texto),
                "messages": []
            }

        chat_id = st.session_state.active_chat_id

        # Guardamos mensaje del usuario con imagen y texto
        buffer = io.BytesIO(imagen.read())
        st.session_state.chats[chat_id]["messages"].append({
            "role": "user",
            "content": f"{texto}",
            "image_bytes": buffer.getvalue()
        })

        # Mostramos "Analizando..."
        with chat_container:
            spinner = st.empty()
            with spinner.container():
                st.markdown("<div class='message-container bot-container'><div class='thinking-animation'>Analizando imagen…</div></div>", unsafe_allow_html=True)

        try:
            headers = {"Authorization": f"Bearer {st.secrets['HUGGINGFACE_API_TOKEN']}"}
            imagen_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            data = {
                "image": imagen_base64,
                "query": texto or "Describe el contenido de esta imagen"
            }
            response = requests.post(
                "https://api-inference.huggingface.co/models/ChatDOC/OCRFlux-3B",
                headers=headers,
                json=data
            )
            if response.ok:
                respuesta_ocr = response.json().get("generated_text", "❌ No se pudo analizar la imagen.")
            else:
                respuesta_ocr = "❌ La API no devolvió respuesta válida."
        except Exception as e:
            respuesta_ocr = f"❌ Error al procesar la imagen: {e}"

        st.session_state.chats[chat_id]["messages"].append({
            "role": "assistant",
            "content": respuesta_ocr
        })

        spinner.empty()
        st.rerun()

    # MODO IMAGEN (generar desde prompt)
    elif st.session_state.modo_generacion == "imagen":
        st.session_state.chats[chat_id]["messages"].append({"role": "user", "content": prompt})

        with chat_container:
            imagen_placeholder = st.empty()
            with imagen_placeholder.container():
                st.markdown("<div class='message-container bot-container'><div class='thinking-animation'>Generando imagen... Esto puede tardar de 1 a 3 minutos.</div></div>", unsafe_allow_html=True)

        try:
            imagen = generar_imagen_flux(prompt, st.secrets["HUGGINGFACE_API_TOKEN"])
            buffer = io.BytesIO()
            imagen.save(buffer, format="PNG")
            st.session_state.chats[chat_id]["messages"].append({
                "role": "assistant",
                "content": "Aquí está tu imagen:",
                "image_bytes": buffer.getvalue()
            })
        except Exception as e:
            st.session_state.chats[chat_id]["messages"].append({
                "role": "assistant",
                "content": f"❌ Error generando imagen: {e}"
            })

        imagen_placeholder.empty()
        st.rerun()

    # MODO TEXTO NORMAL (chat)
    else:
        chat_id = st.session_state.active_chat_id
        st.session_state.chats[chat_id]["messages"].append({"role": "user", "content": prompt})
        st.rerun()
