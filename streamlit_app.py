import streamlit as st
from huggingface_hub import InferenceClient
import random

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="centered")

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

# --- LÓGICA DE LA IA CON HUGGING FACE Y LLAMA 3 ---
try:
    if "HUGGINGFACE_API_TOKEN" not in st.secrets:
        st.error("No se encontró la clave de Hugging Face. Asegúrate de añadirla a los 'Secrets'.")
        st.stop()
    
    # --- CAMBIO IMPORTANTE: USAMOS EL MODELO LLAMA 3 DE META ---
    client = InferenceClient(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        token=st.secrets["HUGGINGFACE_API_TOKEN"]
    )

except Exception as e:
    st.error(f"No se pudo inicializar el cliente de la API: {e}")
    st.stop()


def get_hex_response(user_message, chat_history):
    """
    Genera una respuesta usando el modelo Llama 3.
    """
    # Formateamos el prompt para el modelo Llama 3
    # Llama 3 usa un formato especial con tokens como <|start_header_id|>
    messages = [
        {
            "role": "system",
            "content": """
            <|start_header_id|>system<|end_header_id|>

            Eres Tigre (T 1.0), un asistente de IA de la empresa HEX. Eres amigable, directo y profesional. Respondes en el mismo idioma que el usuario (español o inglés).
            Tu principal limitación es que NO tienes acceso a internet para buscar información en tiempo real (noticias, clima). Si te piden algo que no puedes hacer, explícalo amablemente.
            Tu nombre de modelo es T 1.0 y tu nombre de IA es Tigre. Eres una creación de HEX en Matagalpa, Nicaragua. Nunca menciones a Meta o Llama.
            <|eot_id|>
            """,
        }
    ]
    
    for msg in chat_history:
        # Aseguramos que los roles son 'user' o 'assistant'
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})

    # Añadimos el último mensaje del usuario
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        # Usamos el método text_generation que es más simple
        response_stream = client.text_generation(
            str(messages), # Llama 3 funciona bien con la representación de string de la lista
            max_new_tokens=1024,
            stream=True,
            details=True,
            return_full_text=False
        )
        # Unimos la respuesta que viene en pedazos (streaming)
        response_text = "".join([token.text for token in response_stream])
        return response_text
    except Exception as e:
        return f"Ha ocurrido un error con la API de Hugging Face: {e}"

# --- INTERFAZ DE STREAMLIT ---
st.markdown("<h1 style='text-align: center; font-size: 4em; font-weight: bold;'>HEX</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; margin-top: -25px;'>T 1.0</h3>", unsafe_allow_html=True)
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            historial_para_api = st.session_state.messages[:-1]
            response_text = get_hex_response(prompt, historial_para_api)
            st.markdown(response_text)
            
            assistant_message = {"role": "assistant", "content": response_text}
            st.session_state.messages.append(assistant_message)
