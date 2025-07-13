import streamlit as st
from huggingface_hub import InferenceClient
import time
import random
from PIL import Image
import io
import requests

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    /* Estilos para burbujas de chat, etc. */
    .chat-bubble {
        padding: 12px 18px; border-radius: 20px; margin-bottom: 10px;
        max-width: 75%; word-wrap: break-word; clear: both;
    }
    .user-bubble { float: right; background-color: #f0f0f0; color: #333; }
    .bot-bubble { float: left; background-color: #2b2d31; color: #fff; }
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Sobre HEX T 1.0")
    st.markdown("""
    **T 1.0** es un prototipo de asistente de IA multimodal.
    **Creador:** HEX
    **Sede:** Matagalpa, Nicaragua 🇳🇮
    """)
    st.divider()
    if st.button("Limpiar Historial"):
        st.session_state.messages = []
        st.rerun()

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_client():
    """Obtiene el cliente para el modelo de LENGUAJE (Llama 3)."""
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"Error al inicializar la API de Llama 3: {e}")
        return None

def get_image_caption(image_bytes: bytes, api_token: str) -> str:
    """Obtiene la descripción de una imagen usando el modelo BLIP."""
    API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        response = requests.post(API_URL, headers=headers, data=image_bytes)
        if response.status_code == 200:
            return response.json()[0].get('generated_text', 'No se pudo generar una descripción.')
        else:
            return f"Error al analizar la imagen (Código {response.status_code}): {response.json().get('error', 'Error desconocido')}"
    except Exception as e:
        return f"Error de conexión al analizar la imagen: {e}"

def get_text_response(client, user_message, chat_history):
    """Genera una respuesta de texto usando Llama 3."""
    system_prompt = "<|start_header_id|>system<|end_header_id|>\nEres Tigre (T 1.0), un asistente de IA de HEX. Eres amigable y profesional. Respondes en español. No tienes acceso a internet en tiempo real.<|eot_id|>"
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})

    try:
        full_response = "".join([chunk.choices[0].delta.content for chunk in client.chat_completion(messages=messages, max_tokens=1024, stream=True) if chunk.choices[0].delta.content])
        return full_response
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"

# --- INICIALIZACIÓN Y GESTIÓN DE ESTADO ---
client_ia = get_client()
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.title("HEX T 1.0")

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Si el mensaje es una imagen, la muestra
        if message.get("type") == "image":
            st.image(message["content"], caption=message.get("caption"), use_column_width=True)
        else: # Si es texto, lo muestra como Markdown
            st.markdown(message["content"])

# --- LÓGICA DE INPUT ---
uploaded_file = st.file_uploader("Sube una imagen para analizar", type=["png", "jpg", "jpeg"])
prompt = st.chat_input("Pregúntale algo a T 1.0...")

# Procesar imagen subida
if uploaded_file:
    with st.spinner("Analizando imagen..."):
        image_bytes = uploaded_file.getvalue()
        hf_token = st.secrets.get("HUGGINGFACE_API_TOKEN")
        
        # Muestra la imagen que el usuario subió
        with st.chat_message("user"):
            st.image(image_bytes, use_column_width=True)
        st.session_state.messages.append({"role": "user", "type": "image", "content": image_bytes})
        
        if hf_token:
            # Llama a la IA de imágenes (BLIP)
            description = get_image_caption(image_bytes, hf_token)
            
            # Muestra la descripción generada por la IA
            with st.chat_message("assistant"):
                st.markdown(description)
            st.session_state.messages.append({"role": "assistant", "content": description})
        else:
            st.error("La clave de API de Hugging Face no está configurada.")

# Procesar prompt de texto
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            if client_ia:
                historial_para_api = [msg for msg in st.session_state.messages if msg.get("type") != "image"]
                response_text = get_text_response(client_ia, prompt, historial_para_api)
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            else:
                st.error("El cliente de la API de texto no está disponible.")
