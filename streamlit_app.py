import streamlit as st
from PIL import Image
import io
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

# --- LÓGICA DE LA IA CON HUGGING FACE ---
try:
    if "HUGGINGFACE_API_TOKEN" not in st.secrets:
        st.error("No se encontró la clave de Hugging Face. Asegúrate de añadirla a los 'Secrets'.")
        st.stop()
    
    client = InferenceClient(
        model="mistralai/Mistral-7B-Instruct-v0.2",
        token=st.secrets["HUGGINGFACE_API_TOKEN"]
    )

except Exception as e:
    st.error(f"No se pudo inicializar el cliente de la API: {e}")
    st.stop()


def get_hex_response(user_message, chat_history):
    """
    Genera una respuesta usando un modelo de Hugging Face con un prompt simple.
    """
    # --- NUEVO PROMPT - MÁS SIMPLE Y DIRECTO ---
    system_prompt = """
    Eres Tigre (T 1.0), un asistente de IA de la empresa HEX. Tu tono es amigable y conversacional. Responde siempre en el mismo idioma que el usuario. 
    Tu capacidad se limita a tu conocimiento interno; no puedes acceder a internet en tiempo real ni analizar imágenes. Si te piden algo que no puedes hacer, explícalo amablemente y sugiere una tarea que sí puedas realizar, como generar ideas o explicar un concepto.
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Añadimos el historial previo
    if chat_history:
        messages.extend(chat_history)
    
    # Añadimos el último mensaje del usuario
    messages.append({"role": "user", "content": user_message})
    
    try:
        # Llamada a la API de Hugging Face
        response = client.chat_completion(
            messages=messages,
            max_tokens=1024, # Aumentamos un poco el límite para respuestas más completas
            stream=False,
        )
        return response.choices[0].message.content
    except Exception as e:
        if "Rate limit reached" in str(e):
            return "⚠️ Se ha alcanzado el límite de uso gratuito por ahora. Por favor, intenta de nuevo en unos minutos."
        elif "Model is overloaded" in str(e) or "Model is currently loading" in str(e):
             return "🤖 El modelo está un poco ocupado o arrancando. Por favor, vuelve a preguntar en un momento."
        return f"Ha ocurrido un error inesperado: {e}"


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
    # Añade el mensaje del usuario al historial primero
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Muestra el mensaje del usuario en la pantalla
    with st.chat_message("user"):
        st.markdown(prompt)

    # Ahora genera y muestra la respuesta del asistente
    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            # Pasamos solo el historial (sin el último mensaje del usuario) a la función
            historial_para_api = st.session_state.messages[:-1]
            
            response_text = get_hex_response(prompt, historial_para_api)
            st.markdown(response_text)
            
            # Añade la respuesta del asistente al historial
            assistant_message = {"role": "assistant", "content": response_text}
            st.session_state.messages.append(assistant_message)
