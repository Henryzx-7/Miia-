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
        word-wrap: break-word;
    }
    .user-message-container {
        display: flex;
        justify-content: flex-end;
        width: 100%;
    }
    .bot-message-container {
        display: flex;
        justify-content: flex-start;
        width: 100%;
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
    """Genera una respuesta de la IA (versión estable sin búsqueda web)."""
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
        stream = client.chat_completion(messages=messages, max_tokens=1024, stream=True)
        return response_generator(stream)
    except Exception as e:
        return iter([f"Ha ocurrido un error con la API: {e}"])

# --- INTERFAZ DE STREAMLIT ---
st.title("HEX T 1.0")

# Contenedor para el historial del chat
chat_container = st.container(height=500, border=False)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostramos el historial usando el nuevo diseño de CSS
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"<div class='user-message-container'><div class='chat-bubble user-bubble'>{message['content']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bot-message-container'><div class='chat-bubble bot-bubble'>{message['content']}</div></div>", unsafe_allow_html=True)

# Input del usuario al final de la página
prompt = st.chat_input("Pregúntale algo a T 1.0...")

# DICCIONARIO PARA RESPUESTAS RÁPIDAS (NIVEL 1)
canned_responses = {
    "hola": ["¡Hola! Soy T 1.0. ¿En qué puedo ayudarte hoy?", "¡Hola! ¿Qué tal? Listo para asistirte."],
    "cómo estás": ["¡Muy bien! Como modelo de IA, siempre estoy al 100%. Gracias por preguntar. ¿En qué te puedo ayudar?", "Funcionando a la perfección. ¿Qué tienes en mente hoy?"],
    "como estas": ["¡Muy bien! Como modelo de IA, siempre estoy al 100%. Gracias por preguntar. ¿En qué te puedo ayudar?", "Funcionando a la perfección. ¿Qué tienes en mente hoy?"],
    "que haces": ["Estoy aquí, listo para ayudarte. Puedes pedirme que genere ideas, explique un tema o escriba algo por ti. ¿Qué necesitas?", "Procesando información y esperando tu próxima instrucción. ¡Dispara!"],
    "qué haces": ["Estoy aquí, listo para ayudarte. Puedes pedirme que genere ideas, explique un tema o escriba algo por ti. ¿Qué necesitas?", "Procesando información y esperando tu próxima instrucción. ¡Dispara!"],
    "gracias": ["¡De nada! Es un placer ayudarte.", "Para eso estoy. ¿Necesitas algo más?"]
}

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"): # Usamos esto solo para el ícono y el contenedor
        prompt_lower = prompt.lower().strip()
        
        # --- FILTRO INTELIGENTE ---
        # NIVEL 1: Respuesta instantánea de diccionario
        if prompt_lower in canned_responses:
            response_text = random.choice(canned_responses[prompt_lower])
            st.markdown(f"<div class='chat-bubble bot-bubble'>{response_text}</div>", unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
            # NIVEL 2: Llamada a la IA para todo lo demás
            with st.spinner("T 1.0 está pensando..."):
                historial_para_api = st.session_state.messages[:-1]
                response_stream = get_hex_response(prompt, historial_para_api)
                
                # Muestra la respuesta en streaming
                bot_response_placeholder = st.empty()
                full_response = ""
                for chunk in response_stream:
                    full_response += chunk
                    bot_response_placeholder.markdown(f"<div class='chat-bubble bot-bubble'>{full_response} ▌</div>", unsafe_allow_html=True)
                bot_response_placeholder.markdown(f"<div class='chat-bubble bot-bubble'>{full_response}</div>", unsafe_allow_html=True)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # st.rerun() puede causar problemas a veces, lo eliminamos para mayor estabilidad
    # en su lugar, la app se actualizará por la interacción del usuario
