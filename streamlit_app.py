import streamlit as st
from huggingface_hub import InferenceClient
import time
import random
from datetime import datetime
import pytz
from duckduckgo_search import DDGS

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    /* ... (Todos tus estilos CSS que ya funcionaban van aquí) ... */
    .user-bubble { background-color: #f0f0f0; color: #333; float: right; /* etc. */ }
    .bot-bubble { background-color: #2b2d31; color: #fff; float: left; /* etc. */ }
</style>
""", unsafe_allow_html=True) # Asegúrate de tener tu bloque CSS completo aquí

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

def search_web_for_context(query: str):
    """Realiza una búsqueda web y devuelve un contexto simple."""
    print(f"🔎 Buscando en la web: '{query}'...")
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, region='wt-wt', safesearch='off', timelimit='w', max_results=3)]
            if not results:
                return "No se encontraron resultados relevantes."
            return "\n\n".join(results)
    except Exception as e:
        return f"Error al intentar buscar en la web: {e}"

def get_hex_response(client, user_message, web_context):
    """La IA ahora solo tiene una tarea: sintetizar la información."""
    system_prompt = f"""
    <|start_header_id|>system<|end_header_id|>
    Eres Tigre (T 1.0), un asistente de IA de HEX. Tu tono es profesional y directo.
    TAREA: Responde la "Pregunta del usuario" usando la "Información de la web" que te proporciono.
    INSTRUCCIONES:
    - Actúa como si TÚ hubieras encontrado la información. No menciones "el contexto" o "la búsqueda".
    - Si la información de la web te permite responder sobre el clima, noticias, o la fecha, hazlo. Esa es tu función.
    - Si la información de la web no es relevante para la pregunta (ej. si el usuario solo saluda), IGNÓRALA y responde de forma conversacional.
    - Responde siempre en español. Nunca menciones a Meta o Llama.
    
    ### INFORMACIÓN DE LA WEB
    {web_context}
    <|eot_id|>
    """
    
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"}]
    
    try:
        full_response = ""
        for chunk in client.chat_completion(messages=messages, max_tokens=1500, stream=True):
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        return full_response
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
    chat_ids = list(st.session_state.chats.keys())
    for chat_id in reversed(chat_ids):
        chat_info = st.session_state.chats[chat_id]
        if st.button(chat_info["name"], key=f"chat_{chat_id}", use_container_width=True):
            st.session_state.active_chat_id = chat_id
            st.rerun()

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.markdown("<h1 style='text-align: center;'>HEX T 1.0</h1>", unsafe_allow_html=True)

active_messages = []
if st.session_state.active_chat_id:
    active_messages = st.session_state.chats[st.session_state.active_chat_id].get("messages", [])

for message in active_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- LÓGICA DE INPUT ---
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    if st.session_state.active_chat_id is None:
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {"name": generate_chat_name(prompt), "messages": []}
    
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": prompt})

    # --- FILTRO INTELIGENTE ---
    prompt_lower = prompt.lower().strip()
    greetings = ["hola", "buenas", "que tal", "cómo estás", "como estas"]
    date_questions = ["qué fecha es", "que fecha es", "dime la fecha"]

    if any(saludo in prompt_lower for saludo in greetings):
        # Nivel 1: Respuesta instantánea a saludos
        response_text = random.choice(["¡Hola! ¿En qué puedo ayudarte hoy?", "¡Hola! Soy Tigre. ¿Qué tienes en mente?", "¡Hola! Estoy listo para asistirte."])
    elif any(fecha in prompt_lower for fecha in date_questions):
        # Nivel 2: Respuesta instantánea de fecha
        response_text = get_current_datetime()
    else:
        # Nivel 3: Búsqueda profunda para todo lo demás
        with st.spinner("T 1.0 está buscando en la web..."):
            web_context = search_web_for_context(prompt)
            if "Error" in web_context:
                response_text = web_context
            else:
                historial_para_api = st.session_state.chats[st.session_state.active_chat_id]["messages"]
                response_text = get_hex_response(client_ia, prompt, historial_para_api, web_context)
    
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": response_text})
    st.rerun()
