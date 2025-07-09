import streamlit as st
from huggingface_hub import InferenceClient
import random
from duckduckgo_search import DDGS
import re
from datetime import datetime
import pytz

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide") # Layout ancho para el chat

# --- ESTILOS CSS PERSONALIZADOS PARA EL CHAT ---
st.markdown("""
<style>
    /* Contenedor principal del chat */
    .st-emotion-cache-1f1G2gn {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        padding: 1rem 1rem 1.5rem 1rem;
        border-top: 1px solid #262730;
    }
    /* Estilo para las burbujas de mensaje */
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 20px;
        margin-bottom: 10px;
        max-width: 70%;
        clear: both;
    }
    /* Mensajes del usuario a la derecha */
    .user-bubble {
        background-color: #2b313e;
        float: right;
    }
    /* Mensajes de la IA a la izquierda */
    .bot-bubble {
        background-color: #4a4a4f;
        float: left;
    }
</style>
""", unsafe_allow_html=True)


# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Sobre HEX T 1.0")
    # ... (contenido de la barra lateral)
    if st.button("Limpiar Historial"):
        st.session_state.messages = []
        st.rerun()

# --- LÓGICA DE LA IA Y FUNCIONES ---
try:
    client = InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
except Exception as e:
    st.error(f"No se pudo inicializar el cliente de la API: {e}")
    st.stop()

def get_current_datetime():
    """Obtiene la fecha y hora actual de Nicaragua."""
    nicaragua_tz = pytz.timezone('America/Managua')
    now = datetime.now(nicaragua_tz)
    # Formateamos la fecha y hora en español
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    fecha = f"{dias[now.weekday()]}, {now.day} de {meses[now.month - 1]} de {now.year}"
    hora = now.strftime('%I:%M %p')
    return f"Claro, la fecha y hora actual en Nicaragua es: **{fecha}, {hora}**."

# ... (Las funciones search_duckduckgo y get_hex_response se mantienen igual que en la última versión) ...
def get_hex_response(user_message, chat_history):
    # La lógica interna de esta función (el prompt para Llama 3) no necesita cambiar.
    # El código principal decidirá si la llama o no.
    # ...
    # Aquí iría el código completo de la función get_hex_response
    # Por brevedad, se omite, pero debe estar aquí el código de la respuesta anterior.
    # Placeholder de respuesta para el ejemplo
    return f"Procesando tu pregunta sobre: {user_message}", []


# --- INTERFAZ PRINCIPAL Y LÓGICA DE CHAT ---
st.title("HEX T 1.0") # Título simple, el diseño lo hacemos con Markdown

if "messages" not in st.session_state:
    st.session_state.messages = []

# Muestra el historial usando el nuevo diseño de CSS
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"<div class='chat-bubble user-bubble'>{message['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bubble bot-bubble'>{message['content']}</div>", unsafe_allow_html=True)

# --- ÁREA DE INPUT ---
input_container = st.container()
with input_container:
    prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # --- LÓGICA DE RESPUESTA CON NUEVO FILTRO DE FECHA/HORA ---
    prompt_lower = prompt.lower().strip()
    
    # Filtro Nivel 0: Fecha y Hora (sin IA)
    if any(s in prompt_lower for s in ["qué fecha es hoy", "que fecha es hoy", "dime la fecha", "qué hora es", "que hora es"]):
        response_text = get_current_datetime()
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    else:
        # Llama a la IA para todo lo demás
        with st.spinner("T 1.0 está pensando..."):
            historial_para_api = st.session_state.messages[:-1]
            response_text, response_sources = get_hex_response(prompt, historial_para_api)
            
            assistant_message = {"role": "assistant", "content": response_text, "sources": response_sources}
            st.session_state.messages.append(assistant_message)
    
    st.rerun()
