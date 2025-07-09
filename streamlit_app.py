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
    client = InferenceClient(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        token=st.secrets["HUGGINGFACE_API_TOKEN"]
    )
except Exception as e:
    st.error(f"No se pudo inicializar el cliente de la API: {e}")
    st.stop()

def get_hex_response(user_message, chat_history):
    system_prompt = """
    <|start_header_id|>system<|end_header_id|>
    Eres Tigre (T 1.0), un asistente de IA de la empresa HEX. Tu tono es amigable, directo y profesional. Respondes siempre en el idioma del usuario. Tu principal limitación es que NO tienes acceso a internet. Si te piden algo que requiera búsqueda (noticias, clima), explícalo amablemente. Nunca menciones a Meta o Llama.<|eot_id|>
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})

    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    def response_generator(stream):
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    try:
        # --- CORRECCIÓN DEFINITIVA: Cambiamos max_new_tokens por max_tokens ---
        stream = client.chat_completion(
            messages=messages,
            max_tokens=1024, # Este era el parámetro con el error
            stream=True
        )
        return response_generator(stream)
    except Exception as e:
        return iter([f"Ha ocurrido un error con la API: {e}"])

# --- INTERFAZ DE STREAMLIT ---
st.title("HEX T 1.0")

chat_container = st.container(height=500, border=False)

if "messages" not in st.session_state:
    st.session_state.messages = []

with chat_container:
    st.write("<div class='chat-container'>", unsafe_allow_html=True)
    for message in st.session_state.messages:
        bubble_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
        st.markdown(f"<div class='chat-bubble {bubble_class}'>{message['content']}</div>", unsafe_allow_html=True)
    st.write("</div>", unsafe_allow_html=True)

prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_message = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            historial_para_api = st.session_state.messages[:-1]
            response_stream = get_hex_response(last_user_message, historial_para_api)
            
            bot_response_placeholder = st.empty()
            full_response = ""
            for chunk in response_stream:
                full_response += chunk
                bot_response_placeholder.markdown(full_response + " ▌")
            bot_response_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
