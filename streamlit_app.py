import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="HEX T 1.0",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- LÓGICA DE LA IA (ADAPTADA) ---
@st.cache_resource
def get_model():
    # Obtenemos la clave API de los "Secrets" de Streamlit
    genai.configure(api_key=st.secrets["AIzaSyAM3ZrUXMPwM8JTlNQPGga0tPvlGOcaHUY"])
    return genai.GenerativeModel('gemini-1.5-flash')

def search_duckduckgo(query: str):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results) if results else "No se encontraron resultados."
    except Exception:
        return "Error al buscar en la web."

def get_hex_response(modelo, user_message, chat_history):
    prompt_intento_rapido = f"""
    Eres "T 1.0", un modelo de lenguaje de la empresa "HEX". Tu identidad es ser un asistente útil, eficiente y directo.
    REGLA CRÍTICA: Si no sabes la respuesta o necesitas información muy reciente, responde ÚNICA Y EXCLUSIVAMENTE con el comando: [BUSCAR: el tema que necesitas buscar]
    Si SÍ sabes la respuesta, simplemente respóndela directamente.
    Historial: {chat_history}
    Mensaje del usuario: "{user_message}"
    """
    
    primera_respuesta = modelo.generate_content(prompt_intento_rapido).text
    
    if "[BUSCAR:" in primera_respuesta:
        termino_a_buscar = re.search(r"\[BUSCAR:\s*(.*?)\]", primera_respuesta).group(1)
        informacion_buscada = search_duckduckgo(termino_a_buscar)
        
        prompt_con_busqueda = f"""
        Eres "T 1.0", de "HEX". Para responder a "{user_message}", solicitaste buscar en la web.
        Contexto encontrado: --- {informacion_buscada} ---
        Ahora, usando este contexto, responde de forma final a la pregunta original del usuario.
        """
        response_final = modelo.generate_content(prompt_con_busqueda).text
        return response_final
    else:
        return primera_respuesta

# --- INTERFAZ DE STREAMLIT ---
st.title("🤖 HEX T 1.0")
st.caption("Un asistente de lenguaje avanzado creado por HEX.")

# Inicializar el historial del chat en la sesión
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input del usuario
if prompt := st.chat_input("Pregúntale algo al modelo T 1.0..."):
    # Añadir y mostrar el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar y mostrar la respuesta del asistente
    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            modelo_ia = get_model()
            # Creamos un historial simple para el prompt
            historial_simple = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            response = get_hex_response(modelo_ia, prompt, historial_simple)
            st.markdown(response)
    
    # Añadir la respuesta del asistente al historial
    st.session_state.messages.append({"role": "assistant", "content": response})
