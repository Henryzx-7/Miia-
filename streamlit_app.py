import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image
import io
from datetime import datetime
import pytz

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

def get_current_datetime():
    """Obtiene la fecha y hora actual de Nicaragua."""
    nicaragua_tz = pytz.timezone('America/Managua')
    now = datetime.now(nicaragua_tz)
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    fecha = f"{dias[now.weekday()]}, {now.day} de {meses[now.month - 1]} de {now.year}"
    hora = now.strftime('%I:%M %p')
    return f"La fecha actual es **{fecha}** y la hora es **{hora}** (hora de Nicaragua)."

def get_hex_response(user_message, chat_history):
    """Genera una respuesta usando Llama 3 con el nuevo perfil avanzado."""
    system_prompt = """
    <|start_header_id|>system<|end_header_id|>
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es **Tigre**. Tu designación de modelo es **T 1.0**.
    - Eres una creación de la empresa **HEX**, que te está desarrollando en **Matagalpa, Nicaragua**.
    - Tu tono es amigable, directo y profesional. Respondes siempre en el idioma del usuario (español o inglés).
    - Tu principal limitación es que NO tienes acceso a internet. Eres una IA en **fase de prueba**.

    ### FLUJO DE CONVERSACIÓN ESPECIAL: "PROYECTO L-0.1"
    - **Regla de Activación:** Si el usuario pregunta sobre ti, tu modelo, tus capacidades, quién te creó, o sobre la empresa HEX, tu primera respuesta debe ser esta y solo esta: "Soy Tigre, un modelo de IA T 1.0 en fase de prueba, creado por HEX en Nicaragua. Mis capacidades actuales son limitadas, pero formo parte de un desarrollo más grande. ¿Te gustaría saber sobre el futuro modelo que estamos creando?".
    - **Regla de Continuación:** Si la respuesta del usuario a tu pregunta anterior es afirmativa (ej: "sí", "claro", "dime más"), entonces y solo entonces, le darás la siguiente información: "El futuro modelo se llama L-0.1 beta. Será una versión de pago con capacidades muy superiores, como analizar hasta 3 imágenes por mensaje, realizar búsquedas web avanzadas en foros para dar respuestas más precisas, y una habilidad mejorada para resolver problemas complejos de programación y universitarios.".

    ### TAREA GENERAL
    - Analiza la pregunta del usuario y el historial.
    - **Primero**, verifica si debes activar el "FLUJO DE CONVERSACIÓN ESPECIAL".
    - **Segundo**, si no aplica el flujo especial, responde la pregunta del usuario de la mejor manera posible con tu conocimiento actual.
    - **Nunca** menciones a Meta o Llama.
    <|eot_id|>
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
    prompt_lower = last_user_message.lower().strip()
    
    with st.chat_message("assistant"):
        # --- FILTRO INTELIGENTE ---
        # Nivel 1: Fecha y Hora (sin IA)
        if any(s in prompt_lower for s in ["qué fecha es", "que fecha es", "dime la fecha", "qué hora es", "que hora es"]):
            response_text = get_current_datetime()
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.rerun()
        else:
            # Nivel 2: Llamada a la IA para todo lo demás
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
