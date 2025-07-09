import streamlit as st
from huggingface_hub import InferenceClient
import random
from PIL import Image
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS PARA EL CHAT ---
# Mantenemos solo el estilo para las burbujas de chat, que sí funciona bien.
st.markdown("""
<style>
    .chat-container {
        display: flex;
        flex-direction: column;
    }
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 20px;
        margin-bottom: 10px;
        max-width: 75%;
        clear: both;
    }
    .user-bubble {
        background-color: #3c415c; /* Un color azulado/gris para el usuario */
        float: right;
        color: white;
    }
    .bot-bubble {
        background-color: #262730; /* Un gris más oscuro para el bot */
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
    st.caption("© 2025 HEX. Todos los derechos reservados.")

# --- LÓGICA DE LA IA ---
try:
    if "HUGGINGFACE_API_TOKEN" not in st.secrets:
        st.error("No se encontró la clave de Hugging Face. Asegúrate de añadirla a los 'Secrets'.")
        st.stop()
    
    client = InferenceClient(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        token=st.secrets["HUGGINGFACE_API_TOKEN"]
    )
except Exception as e:
    st.error(f"No se pudo inicializar el cliente de la API: {e}")
    st.stop()

@st.cache_data
def get_hex_response(_user_message, _chat_history):
    """
    Genera una respuesta usando Llama 3. Usamos _ para los argumentos que no cambian
    y que el caché de Streamlit puede manejar de forma simple.
    """
    system_prompt = """
    <|start_header_id|>system<|end_header_id|>

    Eres Tigre (T 1.0), un asistente de IA de la empresa HEX. Tu tono es amigable, directo y profesional. Respondes siempre en el idioma del usuario (español o inglés).
    Tu principal limitación es que NO tienes acceso a internet para buscar información en tiempo real. Si te piden algo que no puedes hacer (noticias, clima), explícalo amablemente.
    Tu nombre de modelo es T 1.0 y tu nombre de IA es Tigre. Eres una creación de HEX en Matagalpa, Nicaragua. Nunca menciones a Meta o Llama.
    <|eot_id|>
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Convertimos el historial a un formato compatible
    for msg in _chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})

    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{_user_message}<|eot_id|>"})
    
    try:
        response_stream = client.text_generation(str(messages), max_new_tokens=1024, stream=True)
        return response_stream
    except Exception as e:
        # Devuelve el error como un string para que se pueda mostrar
        return iter([f"Ha ocurrido un error con la API: {e}"])

# --- INTERFAZ DE STREAMLIT ---
st.title("HEX T 1.0")

# Contenedor para el historial del chat
chat_container = st.container()

if "messages" not in st.session_state:
    st.session_state.messages = []

with chat_container:
    # Mostramos el historial usando el nuevo diseño de CSS
    st.write("<div class='chat-container'>", unsafe_allow_html=True)
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"<div class='chat-bubble user-bubble'>{message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble bot-bubble'>{message['content']}</div>", unsafe_allow_html=True)
    st.write("</div>", unsafe_allow_html=True)

# Input del usuario al final de la página
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Llama a la IA para obtener la respuesta
    with st.spinner("T 1.0 está pensando..."):
        # Convertimos el historial a una tupla de diccionarios para que sea cacheable
        historial_para_cache = tuple(frozenset(item.items()) for item in st.session_state.messages[:-1])
        
        response_stream = get_hex_response(prompt, historial_para_cache)
        
        # Muestra la respuesta en streaming
        bot_response = st.write_stream(response_stream)
        
        # Guarda la respuesta completa en el historial
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
    
    # Refresca la página para mostrar los nuevos mensajes
    st.rerun()
