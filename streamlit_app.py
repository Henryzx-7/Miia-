import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
from google.api_core import exceptions as google_exceptions

st.set_page_config(page_title="HEX T 1.0 - MODO DIAGNÓSTICO", page_icon="ախ", layout="centered")

st.info("MODO DE DIAGNÓSTICO ACTIVADO")

# --- PASO 1: Configuración de API ---
st.write("Punto de Control 1: Intentando configurar la API de Google...")
try:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("ERROR CRÍTICO: No se encontró la clave GEMINI_API_KEY en los secretos.")
        st.stop()
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    st.write("✅ Punto de Control 1: API configurada.")
except Exception as e:
    st.error(f"ERROR EN PUNTO 1: {e}")
    st.stop()

# --- PASO 2: Obteniendo el modelo ---
@st.cache_resource
def get_model():
    st.write("Punto de Control 2: Intentando obtener el modelo de IA (esto solo debería pasar una vez).")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        st.write("✅ Punto de Control 2: Modelo obtenido.")
        return model
    except Exception as e:
        st.error(f"ERROR EN PUNTO 2: {e}")
        return None

modelo_ia = get_model()
if not modelo_ia:
    st.stop()

# --- INTERFAZ ---
st.title("🤖 HEX T 1.0")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Escribe tu pregunta...")

# Lista de palabras para el filtro
canned_responses = {
    "hola": "¡Hola! Soy T 1.0. (Respuesta rápida sin IA)",
    "cómo estás": "¡Muy bien! (Respuesta rápida sin IA)",
    "como estas": "¡Muy bien! (Respuesta rápida sin IA)",
    "gracias": "¡De nada! (Respuesta rápida sin IA)"
}

if prompt:
    st.write(f"Punto de Control 3: Se recibió un prompt del usuario: '{prompt}'")
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        prompt_lower = prompt.lower().strip()
        
        # --- LÓGICA DEL FILTRO ---
        st.write("Punto de Control 4: Evaluando el filtro inteligente...")
        if prompt_lower in canned_responses:
            st.write("✅ Punto de Control 4: El prompt es un saludo. Tomando el camino rápido.")
            response_text = canned_responses[prompt_lower]
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
            # --- CAMINO PROFUNDO (LLAMADA A LA API) ---
            st.write("Punto de Control 5: El prompt es una pregunta real. Preparando para llamar a la API.")
            with st.spinner("Llamando a la IA..."):
                try:
                    # Simplificamos la llamada para el diagnóstico
                    st.write("Punto de Control 6: ¡Llamando a la API de Gemini AHORA!")
                    response = modelo_ia.generate_content(f"Responde a esto de forma breve: {prompt}")
                    response_text = response.text
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                except google_exceptions.ResourceExhausted:
                    st.error("ERROR DEFINITIVO: Se alcanzó el límite de recursos (ResourceExhausted).")
                except Exception as e:
                    st.error(f"ERROR DEFINITIVO: Ocurrió un error inesperado durante la llamada a la API: {e}")
else:
    st.write("Punto de Control 7: La página se cargó, esperando un prompt del usuario.")
