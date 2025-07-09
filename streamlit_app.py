import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
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

def get_hex_response(user_message, chat_history):
    """
    Genera una respuesta usando Llama 3 con el método correcto (chat_completion).
    """
    system_prompt = """
    <|start_header_id|>system<|end_header_id|>
    Eres Tigre (T 1.0), un asistente de IA de la empresa HEX. Tu tono es amigable, directo y profesional. Respondes siempre en el idioma del usuario. Tu principal limitación es que NO tienes acceso a internet. Si te piden algo que requiera búsqueda (noticias, clima), explícalo amablemente. Nunca menciones a Meta o Llama.<|eot_id|>
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Formateo del historial para Llama 3
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})

    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    # Generador para el streaming de la respuesta
    def response_generator(stream):
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    try:
        # --- CORRECCIÓN DEFINITIVA: Usamos chat_completion con stream ---
        stream = client.chat_completion(
            messages=messages,
            max_new_tokens=1024,
            stream=True
        )
        return response_generator(stream)
    except Exception as e:
        # Devuelve el error como un generador para que se pueda mostrar
        error_message = f"Ha ocurrido un error con la API: {e}"
        return iter([error_message])

# --- INTERFAZ DE STREAMLIT ---
st.title("HEX T 1.0")

# Contenedor para el historial del chat
chat_container = st.container(height=500, border=False)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostramos el historial usando el nuevo diseño de CSS
with chat_container:
    st.write("<div class='chat-container'>", unsafe_allow_html=True)
    for message in st.session_state.messages:
        bubble_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
        st.markdown(f"<div class='chat-bubble {bubble_class}'>{message['content']}</div>", unsafe_allow_html=True)
    st.write("</div>", unsafe_allow_html=True)

# Input del usuario al final de la página
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    # Añade y muestra el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Refresca la página para mostrar el mensaje del usuario inmediatamente
    st.rerun()

# Lógica para generar la respuesta del asistente
# Se ejecuta solo si el último mensaje fue del usuario
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_message = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            # Pasamos el historial (sin el último mensaje del usuario) a la función
            historial_para_api = st.session_state.messages[:-1]
            
            response_stream = get_hex_response(last_user_message, historial_para_api)
            
            # Muestra la respuesta en streaming
            bot_response_placeholder = st.empty()
            full_response = ""
            for chunk in response_stream:
                full_response += chunk
                bot_response_placeholder.markdown(full_response + " ▌")
            bot_response_placeholder.markdown(full_response)
    
    # Guarda la respuesta completa en el historial
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Refresca la página para limpiar el estado de "último mensaje fue del usuario"
    st.rerun()
