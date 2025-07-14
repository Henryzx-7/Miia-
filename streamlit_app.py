import streamlit as st
from huggingface_hub import InferenceClient
import time
import random
from datetime import datetime
import pytz
import re
import html

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS Y JAVASCRIPT ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Space+Grotesk:wght@700&display=swap');

    .animated-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 4em; font-weight: 700; text-align: center; color: #888;
        background: linear-gradient(90deg, #555, #fff, #555);
        background-size: 200% auto;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shine 5s linear infinite;
    }
    .subtitle { text-align: center; margin-top: -25px; font-size: 1.5em; color: #aaa; }
    @keyframes shine { to { background-position: -200% center; } }

    .message-container { display: flex; width: 100%; margin-bottom: 10px; animation: fadeIn 0.5s ease-in-out; }
    .user-container { justify-content: flex-end; }
    .bot-container { justify-content: flex-start; }
    .chat-bubble { padding: 12px 18px; border-radius: 20px; max-width: 75%; word-wrap: break-word; }
    .user-bubble { background-color: #f0f0f0; color: #333; }
    .bot-bubble { background-color: #2b2d31; color: #fff; }

    .thinking-animation { font-style: italic; color: #888; }

    .code-block-container { position: relative; background-color: #1e1e1e; border-radius: 8px; margin: 1rem 0; }
    .code-block-header { display: flex; justify-content: space-between; align-items: center; background-color: #333; padding: 8px 12px; border-top-left-radius: 8px; border-top-right-radius: 8px;}
    .copy-button { background-color: #555; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; }
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
<script>
    async function copyToClipboard(elementId) {
        const codeElement = document.getElementById(elementId);
        if (codeElement) {
            try {
                await navigator.clipboard.writeText(codeElement.innerText);
            } catch (err) {
                console.error('Error al copiar:', err);
            }
        }
    }
</script>
""", unsafe_allow_html=True)

# --- LÓGICA DE LA IA Y FUNCIONES AUXILIARES ---
@st.cache_resource
def get_client():
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"Error al inicializar la API: {e}")
        return None

def get_current_datetime():
    now_utc = datetime.now(pytz.utc)
    return f"Claro, la fecha universal (UTC) de hoy es **{now_utc.strftime('%A, %d de %B de %Y')}**."

from duckduckgo_search import DDGS
def search_web(query: str):
    print(f"🔎 Buscando en la web: '{query}'...")
    try:
        with DDGS() as ddgs:
            results = [{"snippet": r['body'], "url": r['href']} for r in ddgs.text(query, region='wt-wt', max_results=3)]
            if not results: return "No se encontraron resultados relevantes.", []
            context = "\n\n".join([f"Fuente: {r['snippet']}" for r in results])
            sources = [r for r in results]
            return context, sources
    except Exception as e:
        return f"Error al buscar en la web: {e}", []

def get_hex_response(client, user_message, web_context):
    system_prompt = f"""<|start_header_id|>system<|end_header_id|>
    Eres Tigre (T 1.0), un asistente de IA de HEX. Tu tono es formal y preciso.
    TAREA: Responde la "Pregunta del usuario" usando la "Información de la web". Actúa como si TÚ hubieras encontrado esta información. No menciones "el contexto".
    INSTRUCCIONES:
    - Si la información es relevante (noticias, clima, etc.), úsala para dar una respuesta directa y actualizada.
    - Si la información no es relevante (ej. si el usuario solo saluda), IGNÓRALA y responde de forma conversacional.
    - Responde siempre en español. Nunca menciones a Meta o Llama.

    ### INFORMACIÓN DE LA WEB
    {web_context}<|eot_id|>"""
    
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"}]
    
    try:
        response = client.chat_completion(messages=messages, max_tokens=1500, stream=False)
        return response.choices[0].message.content
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"

def generate_chat_name(first_prompt):
    name = str(first_prompt).split('\n')[0]
    return name[:30] + "..." if len(name) > 30 else name

# --- INICIALIZACIÓN Y GESTIÓN DE ESTADO ---
client_ia = get_client()
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Conversaciones")
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.active_chat_id = None
        st.rerun()
    st.divider()
    # (Aquí va la lógica del historial en la barra lateral que ya funcionaba)

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.markdown("<div class='animated-title'>HEX</div><p class='subtitle'>T 1.0</p>", unsafe_allow_html=True)

if st.session_state.active_chat_id:
    for message in st.session_state.chats[st.session_state.active_chat_id]["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("Fuentes Consultadas"):
                    for source in message["sources"]:
                        st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")

# Lógica de Input
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    if st.session_state.active_chat_id is None:
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {"name": generate_chat_name(prompt), "messages": []}
    
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": prompt})

    # --- LÓGICA DE RESPUESTA CON FILTRO Y BÚSQUEDA AUTOMÁTICA ---
    prompt_lower = prompt.lower().strip()
    greetings = ["hola", "buenas", "que tal", "cómo estás", "como estas"]
    date_questions = ["qué fecha es", "que fecha es", "dime la fecha"]

    if any(saludo in prompt_lower for saludo in greetings):
        response_text = random.choice(["¡Hola! Soy Tigre. ¿En qué puedo ayudarte?", "¡Hola! ¿Qué tal?"])
        response_sources = []
    elif any(fecha in prompt_lower for fecha in date_questions):
        response_text = get_current_datetime()
        response_sources = []
    else:
        # Para todo lo demás, busca en la web
        with st.spinner("T 1.0 está buscando en la web..."):
            web_context, sources = search_web(prompt)
            if "Error" in web_context:
                response_text = web_context
                response_sources = []
            else:
                historial_para_api = st.session_state.chats[st.session_state.active_chat_id]["messages"]
                response_text = get_hex_response(client_ia, prompt, historial_para_api, web_context)
                response_sources = sources
    
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({
        "role": "assistant",
        "content": response_text,
        "sources": response_sources
    })
    st.rerun()
