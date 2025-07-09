import streamlit as st
from huggingface_hub import InferenceClient
import random
from PIL import Image
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS PARA EL CHAT ---
st.markdown("""
<style>
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 20px;
        margin-bottom: 10px;
        max-width: 75%;
        clear: both;
    }
    .user-bubble {
        background-color: #3c415c;
        float: right;
        color: white;
    }
    .bot-bubble {
        background-color: #262730;
        float: left;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Sobre HEX T 1.0")
    st.markdown("""
    **T 1.0** es un prototipo de asistente de IA.
    **Creador:** HEX
    **Sede:** Matagalpa, Nicaragua 🇳🇮
    """)
    st.divider()
    if st.button("Limpiar Historial"):
        st.session_state.messages = []
        st.rerun()

# --- LÓGICA DE LA IA ---
try:
    # Se inicializa el cliente de la API de forma segura
    client = InferenceClient(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        token=st.secrets["HUGGINGFACE_API_TOKEN"]
    )
except Exception as e:
    st.error(f"No se pudo inicializar el cliente de la API: {e}")
    st.stop()

# Eliminamos @st.cache_data para evitar el TypeError
def get_hex_response(user_message, chat_history):
    """Genera una respuesta usando Llama 3."""
    system_prompt = """
    <|start_header_id|>system<|end_header_id|>
    Eres Tigre (T 1.0), un asistente de IA de la empresa HEX. Tu tono es amigable, directo y profesional. Respondes siempre en el idioma del usuario. Tu principal limitación es que NO tienes acceso a internet. Si te piden algo que requiera búsqueda (noticias, clima), explícalo amablemente.
    <|eot_id|>
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        # Usamos el método text_generation en modo streaming para una respuesta más rápida
        response_stream = client.text_generation(
            str(messages),
            max_new_tokens=1024,
            stream=True,
            details=True,
            return_full_text=False
        )
        return response_stream
    except Exception as e:
        return iter([f"Ha ocurrido un error con la API: {e}"])

# --- INTERFAZ DE STREAMLIT ---
st.title("HEX T 1.0")

# Contenedor para el historial del chat
chat_container = st.container(height=500, border=False)

if "messages" not in st.session_state:
    st.session_state.messages = []

with chat_container:
    for message in st.session_state.messages:
        # Usamos el diseño de CSS personalizado
        if message["role"] == "user":
            st.markdown(f"<div class='chat-bubble user-bubble'>{message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble bot-bubble'>{message['content']}</div>", unsafe_allow_html=True)

# Input del usuario al final de la página
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    # Añade y muestra el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container:
        st.markdown(f"<div class='chat-bubble user-bubble'>{prompt}</div>", unsafe_allow_html=True)
    
    # Genera y muestra la respuesta del asistente en streaming
    with chat_container:
        with st.chat_message("assistant"):
            # Usamos un contenedor vacío para ir "escribiendo" la respuesta
            response_placeholder = st.empty()
            full_response = ""
            # Llamamos a la IA
            response_stream = get_hex_response(prompt, st.session_state.messages)
            for chunk in response_stream:
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            # Mostramos la respuesta final sin el cursor
            response_placeholder.markdown(full_response)
    
    # Guarda la respuesta completa en el historial de la sesión
    st.session_state.messages.append({"role": "assistant", "content": full_response})
