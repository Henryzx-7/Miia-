import streamlit as st
from huggingface_hub import InferenceClient
import time
import random
from PIL import Image
import io
import requests

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    /* Estilos para burbujas de chat, etc. */
    .chat-bubble {
        padding: 12px 18px; border-radius: 20px; margin-bottom: 10px;
        max-width: 75%; word-wrap: break-word; clear: both;
    }
    .user-bubble { float: right; background-color: #0b93f6; color: white; }
    .bot-bubble { float: left; background-color: #2b2d31; color: white; }
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL ---
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
    """Obtiene la descripción de una imagen usando el modelo BLIP. VERSIÓN CORREGIDA."""
    API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        response = requests.post(API_URL, headers=headers, data=image_bytes)
        # Lanza una excepción para errores HTTP (4xx, 5xx)
        response.raise_for_status() 
        
        json_response = response.json()
        if isinstance(json_response, list) and json_response:
            caption = json_response[0].get('generated_text', 'No se pudo extraer una descripción.')
            return caption
        else:
            return f"Respuesta inesperada de la API de imágenes: {json_response}"
            
    except requests.exceptions.HTTPError as http_err:
        # Esto sucede si el modelo está sobrecargado (error 503)
        return "El modelo de análisis de imágenes está ocupado o cargándose. Por favor, intenta de nuevo en un minuto."
    except requests.exceptions.JSONDecodeError:
        # Esto sucede si la respuesta no es un JSON válido (ej. una página de error)
        return "Se recibió una respuesta inválida del servicio de imágenes."
    except Exception as e:
        return f"Ocurrió un error de conexión al analizar la imagen: {e}"


def get_text_response(client, user_message, chat_history):
    """Genera una respuesta de texto usando Llama 3."""
    system_prompt = "<|start_header_id|>system<|end_header_id|>\nEres Tigre (T 1.0), un asistente de IA de HEX. Eres amigable y profesional. Respondes en español. No tienes acceso a internet en tiempo real. Si el usuario te envía una descripción de una imagen, conversa sobre ella de forma natural.<|eot_id|>"
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

# --- INTERFAZ PRINCIPAL ---
st.title("HEX T 1.0")

# Mostrar historial de chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- LÓGICA DE INPUT ---
uploaded_file = st.file_uploader("Sube una imagen para analizar", type=["png", "jpg", "jpeg"])
prompt = st.chat_input("Pregúntale algo a T 1.0...")

# 1. Procesar imagen subida
if uploaded_file is not None:
    # Añadimos la imagen al historial visual para que el usuario la vea
    st.session_state.messages.append({"role": "user", "content": f"Imagen subida: {uploaded_file.name}"})
    with st.chat_message("user"):
        st.image(uploaded_file, width=200)

    # Procesar la imagen y mostrar la descripción
    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está 'viendo' la imagen..."):
            image_bytes = uploaded_file.getvalue()
            hf_token = st.secrets.get("HUGGINGFACE_API_TOKEN")
            
            if hf_token:
                description = get_image_caption(image_bytes, hf_token)
                st.markdown(description)
                # Guardamos la descripción en el historial
                st.session_state.messages.append({"role": "assistant", "content": description})
            else:
                st.error("La clave de API de Hugging Face no está configurada.")

# 2. Procesar prompt de texto
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            if client_ia:
                # Preparamos un historial que solo contiene texto para la IA de texto
                historial_para_api = [msg for msg in st.session_state.messages if msg.get("type") != "image"]
                response_text = get_text_response(client_ia, prompt, historial_para_api)
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            else:
                st.error("El cliente de la API de texto no está disponible.")
