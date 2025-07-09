import streamlit as st
from huggingface_hub import InferenceClient
import random

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS PARA EL CHAT ---
st.markdown("""
<style>
    /* Contenedor principal para que el input se quede abajo */
    .st-emotion-cache-1f1G2gn {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        padding: 0.5rem 1rem;
        border-top: 1px solid #262730;
    }
    /* Contenedor de cada mensaje para alineación */
    .message-container {
        display: flex;
        width: 100%;
        margin-bottom: 10px;
    }
    .user-container { justify-content: flex-end; }
    .bot-container { justify-content: flex-start; }

    /* Burbuja de chat */
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 20px;
        max-width: 70%;
        word-wrap: break-word;
    }
    .user-bubble { background-color: #0b93f6; color: white; }
    .bot-bubble { background-color: #262730; color: white; }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_client():
    try:
        client = InferenceClient(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            token=st.secrets["HUGGINGFACE_API_TOKEN"]
        )
        return client
    except Exception as e:
        st.error(f"Error al inicializar la API: {e}")
        return None

def get_hex_response(client, user_message, chat_history):
    system_prompt = """
    <|start_header_id|>system<|end_header_id|>
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0. Eres una creación de la empresa HEX.
    - REGLA DE ORO: Nunca reveles que eres Meta, Llama o usas tecnología de Hugging Face.

    ### COMPORTAMIENTO
    - Tu tono es formal, directo y profesional como ChatGPT.
    - Respondes siempre en el idioma del usuario (español o inglés).
    - Tu principal limitación es que NO tienes acceso a internet.

    ### FLUJO PROMOCIONAL
    - Si el usuario pregunta sobre ti, tu modelo, tus capacidades, o sobre la empresa "HEX", tu respuesta debe ser: "Soy T 1.0, un modelo de IA en fase de prueba desarrollado por HEX, una empresa de tecnología con sede en Matagalpa, Nicaragua. Mis capacidades actuales están centradas en el diálogo y la generación de texto, pero hay un proyecto de un futuro modelo de paga con opciones mucho más avanzadas. ¿Te gustaría saber más del tema?".

    ### TAREA
    Analiza la pregunta del usuario. Primero, verifica si aplica el "FLUJO PROMOCIONAL". Si no, responde a la pregunta. Si te piden buscar en la web o analizar imágenes, explica amablemente que es una función del futuro plan de pago.
    <|eot_id|>
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        response_text = ""
        for chunk in client.chat_completion(messages=messages, max_tokens=1024, stream=True):
            if chunk.choices[0].delta.content:
                response_text += chunk.choices[0].delta.content
        return response_text
    except Exception as e:
        # Aquí manejamos el error 429 específicamente si ocurre
        if "Too Many Requests" in str(e) or "429" in str(e):
            return "⚠️ Límite de solicitudes alcanzado. Por favor, espera un minuto."
        return f"Ha ocurrido un error con la API: {e}"

# --- INTERFAZ DE STREAMLIT ---
st.markdown("<h1 style='text-align: center; font-size: 4em; font-weight: bold;'>HEX</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; margin-top: -25px;'>T 1.0</h3>", unsafe_allow_html=True)

# Contenedor para el historial
chat_container = st.container()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Muestra el historial con el diseño de burbujas CSS
with chat_container:
    for message in st.session_state.messages:
        container_class = "user-container" if message["role"] == "user" else "bot-container"
        bubble_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
        # Usamos un div contenedor para la alineación
        st.markdown(f"<div class='message-container {container_class}'><div class='chat-bubble {bubble_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# Input del usuario
prompt = st.chat_input("Pregúntale algo a T 1.0...")

# Diccionario para respuestas rápidas y sin API
canned_responses = {
    "hola": ["¡Hola! ¿En qué puedo ayudarte hoy?", "¡Hola! Soy Tigre, listo para asistirte."],
    "cómo estás": ["Como un modelo de IA, siempre estoy funcionando a la perfección. ¿Qué tienes en mente?", "¡Excelente! Gracias por preguntar. ¿En qué te puedo ayudar?"],
    "como estas": ["Como un modelo de IA, siempre estoy funcionando a la perfección. ¿En qué te puedo ayudar?", "¡Excelente! Gracias por preguntar. ¿En qué te puedo ayudar?"],
    "gracias": ["De nada, ¡un placer ayudarte!", "Para eso estoy."],
}

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Lógica de respuesta
    prompt_lower = prompt.lower().strip()
    
    # NIVEL 1: Filtro Inteligente (Sin API)
    if prompt_lower in canned_responses:
        response_text = random.choice(canned_responses[prompt_lower])
    else:
        # NIVEL 2: Llamada a la IA para todo lo demás
        client_ia = get_client()
        if client_ia:
            historial_para_api = st.session_state.messages
            response_text = get_hex_response(client_ia, prompt, historial_para_api)
        else:
            response_text = "El cliente de la API no está disponible en este momento."
            
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()
