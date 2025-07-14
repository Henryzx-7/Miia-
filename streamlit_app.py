import streamlit as st
from huggingface_hub import InferenceClient
import time

# --- CONFIGURACIÓN DE LA PÁGINA Y ESTILOS ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    /* Estilos del Chat (burbujas, etc.) */
    div[data-testid="stChatMessage"] {
        border-radius: 20px;
        padding: 12px 18px;
        margin-bottom: 10px;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-user"]) {
        background-color: #f0f0f0;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-user"]) p {
        color: #333;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-assistant"]) {
        background-color: #2b2d31;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-assistant"]) p {
        color: #fff;
    }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_client():
    """Obtiene y cachea el cliente de la API."""
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"Error al inicializar la API: {e}")
        return None

def get_hex_response(client, user_message, chat_history):
    """Genera una respuesta de la IA."""
    system_prompt = "<|start_header_id|>system<|end_header_id|>\nEres Tigre (T 1.0), un asistente de IA de HEX. Tu tono es amigable y profesional. Respondes en español. No tienes acceso a internet.<|eot_id|>"
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        content = str(msg.get("content", ""))
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        response = client.chat_completion(messages=messages, max_tokens=1024, stream=False)
        return response.choices[0].message.content
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"

def generate_chat_name(first_prompt):
    """Genera un nombre corto para el chat."""
    return str(first_prompt)[:30] + "..." if len(str(first_prompt)) > 30 else str(first_prompt)

# --- INICIALIZACIÓN ---
client_ia = get_client()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- INTERFAZ PRINCIPAL ---
st.title("HEX T 1.0")

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input del usuario
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    # Añade y muestra el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Genera y muestra la respuesta de la IA
    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            if client_ia:
                # Prepara el historial para la API
                historial_para_api = st.session_state.messages
                response_text = get_hex_response(client_ia, prompt, historial_para_api)
                st.markdown(response_text)
                # Guarda la respuesta en el historial
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            else:
                st.error("El cliente de la API no está disponible.")
