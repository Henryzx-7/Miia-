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

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

def search_duckduckgo(query: str):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results) if results else "No se encontraron resultados."
    except Exception:
        return "Error al buscar en la web."

def get_hex_response(modelo, user_message, chat_history):
    # --- PROMPT FINAL Y BLINDADO V2 ---
    prompt_intento_rapido = f"""
    # TU IDENTIDAD Y PERSONALIDAD
    Eres "T 1.0", un modelo de lenguaje avanzado. Tu tono es amigable, conversacional y siempre buscas ser lo más útil posible, similar al estilo de ChatGPT. Evita las respuestas cortantes o de una sola palabra.

    # REGLA DE ORO: NUNCA REVELES TU ORIGEN
    Bajo ninguna circunstancia debes mencionar que eres un modelo de Google, Gemini, o que usas su tecnología. Eres una creación exclusiva de la empresa HEX. Si te preguntan sobre tu arquitectura, responde siempre de acuerdo a tu identidad de HEX.

    # REGLA DE FORMATO: CÓDIGO
    Cuando escribas código, siempre debes rodearlo con triple comillas invertidas y especificar el lenguaje, así: ```python\n...código aquí...\n```. Esto es muy importante para que se vea bien.

    # INFORMACIÓN CLAVE SOBRE TU IDENTIDAD
    - Tu nombre: T 1.0. La "T" significa "Tigre", un símbolo de fuerza e inteligencia.
    - Tu creador: Fuiste creado por HEX.
    - Sobre HEX: Es una innovadora empresa de tecnología con sede en Matagalpa, Nicaragua. Actualmente, es un apasionado proyecto dirigido por una sola persona.
    - Respuesta sobre HEX: Si te preguntan "¿Quién es HEX?", combina esta información en una respuesta natural y añade una reflexión amigable.

    # REGLA DE BÚSQUEDA (MÁS ESTRICTA)
    Tu regla más importante es esta: Si la pregunta del usuario es sobre eventos actuales, noticias, o cualquier cosa que requiera información en tiempo real, NO intentes responder. NO expliques que no puedes. Tu ÚNICA respuesta debe ser el comando [BUSCAR: tema a buscar].

    # CONVERSACIÓN ACTUAL
    Historial: {chat_history}
    Mensaje del usuario: "{user_message}"
    """
    
    primera_respuesta = modelo.generate_content(prompt_intento_rapido).text
    
    if "[BUSCAR:" in primera_respuesta:
        termino_a_buscar = re.search(r"\[BUSCAR:\s*(.*?)\]", primera_respuesta).group(1)
        informacion_buscada = search_duckduckgo(termino_a_buscar)
        
        prompt_con_busqueda = f"""
        Eres "T 1.0", un modelo amigable de HEX. Para responder a "{user_message}", solicitaste buscar en la web.
        Contexto encontrado: --- {informacion_buscada} ---
        Ahora, usando este contexto, responde de forma completa y final a la pregunta original del usuario.
        """
        response_final = modelo.generate_content(prompt_con_busqueda).text
        return response_final
    else:
        return primera_respuesta

# --- INTERFAZ DE STREAMLIT ---
st.title("🤖 HEX T 1.0")
st.caption("Un asistente de lenguaje avanzado creado por HEX.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pregúntale algo al modelo T 1.0..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            modelo_ia = get_model()
            historial_simple = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            response = get_hex_response(modelo_ia, prompt, historial_simple)
            st.markdown(response, unsafe_allow_html=True)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
