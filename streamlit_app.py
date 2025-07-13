import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image
import io
import time
import random
import requests # <-- Importante añadir esta librería

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    /* Estilos para el contenedor principal del chat y las burbujas */
    .st-emotion-cache-1f1G2gn {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        padding: 1rem 1rem 1.5rem 1rem;
        border-top: 1px solid #262730;
    }
    .chat-bubble {
        padding: 12px 18px; border-radius: 20px; margin-bottom: 10px;
        max-width: 75%; word-wrap: break-word; clear: both;
    }
    .user-bubble { float: right; background-color: #0b93f6; color: white; }
    .bot-bubble { float: left; background-color: #2b2d31; color: white; }
</style>
""", unsafe_allow_html=True)


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
    API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        response = requests.post(API_URL, headers=headers, data=image_bytes)
        if response.status_code == 200:
            return response.json()[0].get('generated_text', 'No se pudo generar una descripción.')
        else:
            return f"Error al analizar la imagen (Código {response.status_code}): {response.json().get('error', 'El modelo de imágenes puede estar cargándose. Intenta de nuevo en un minuto.')}"
    except Exception as e:
        return f"Error de conexión al analizar la imagen: {e}"

def get_text_response(client, user_message, chat_history):
    """Genera una respuesta de texto usando Llama 3."""
    system_prompt = "<|start_header_id|>system<|end_header_id|>\nEres Tigre (T 1.0), un asistente de IA de HEX. Eres amigable y profesional. Respondes en español. No tienes acceso a internet. Si el usuario te envía una descripción de una imagen, conversa sobre ella de forma natural.<|eot_id|>"
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
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
st.caption("Asistente de IA por HEX")
st.divider()

# Mostrar historial de chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Contenedor para el input y el botón de carga
input_container = st.container()
with input_container:
    col1, col2 = st.columns([1, 8])
    with col1:
        uploaded_file = st.file_uploader(" ", label_visibility="collapsed", type=["png", "jpg", "jpeg"])
    with col2:
        prompt = st.chat_input("Pregúntale algo a T 1.0...")

# --- LÓGICA DE PROCESAMIENTO ---
# 1. Procesar imagen subida
if uploaded_file:
    with st.chat_message("user"):
        st.image(uploaded_file, width=200)
    
    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está 'viendo' la imagen..."):
            image_bytes = uploaded_file.getvalue()
            hf_token = st.secrets.get("HUGGINGFACE_API_TOKEN")
            if hf_token:
                description = get_image_caption(image_bytes, hf_token)
                # Creamos un prompt para que la IA principal comente la descripción
                prompt_for_llama = f"Acabo de subir una imagen y el sistema de visión la describe así: '{description}'. ¿Qué piensas o qué detalles interesantes puedes añadir?"
                
                with st.spinner("T 1.0 está pensando sobre la imagen..."):
                    historial_para_api = st.session_state.messages
                    response_text = get_text_response(client_ia, prompt_for_llama, historial_para_api)
                    st.markdown(response_text)
                    # Guardar ambos mensajes en el historial
                    st.session_state.messages.append({"role": "user", "content": f"(Imagen subida: {uploaded_file.name})"})
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

# 2. Procesar prompt de texto
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            historial_para_api = st.session_state.messages[:-1]
            response_text = get_text_response(client_ia, prompt, historial_para_api)
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
