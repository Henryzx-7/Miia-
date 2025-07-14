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

# --- ESTILOS CSS Y JAVASCRIPT COMPLETOS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Space+Grotesk:wght@700&display=swap');

    /* Encabezado animado */
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

    /* Contenedores y Burbujas de Chat (ESTILO CORREGIDO) */
    .message-container { display: flex; width: 100%; margin-bottom: 10px; animation: fadeIn 0.5s ease-in-out; }
    .user-container { justify-content: flex-end; }
    .bot-container { justify-content: flex-start; }
    .chat-bubble { padding: 12px 18px; border-radius: 20px; max-width: 75%; word-wrap: break-word; }
    .user-bubble { background-color: #f0f0f0; color: #333; }
    .bot-bubble { background-color: #2b2d31; color: #fff; }

    /* Animación de "Pensando..." */
    .thinking-animation { font-style: italic; color: #888; }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
""", unsafe_allow_html=True)


# --- LÓGICA DE LA IA Y FUNCIONES AUXILIARES ---
@st.cache_resource
def get_client():
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"Error al inicializar la API: {e}")
        return None

# Mantenemos la lógica de búsqueda que habíamos quitado
from duckduckgo_search import DDGS

def search_web(query: str):
    """Realiza una búsqueda web y devuelve contexto y fuentes."""
    print(f"🔎 Buscando en la web: '{query}'...")
    try:
        with DDGS() as ddgs:
            results = [{"snippet": r['body'], "url": r['href']} for r in ddgs.text(query, region='wt-wt', max_results=3)]
            if not results: return "No se encontraron resultados relevantes.", []
            context_text = "\n\n".join([f"Fuente: {r['snippet']}" for r in results])
            sources = [r['url'] for r in results]
            return context_text, sources
    except Exception as e:
        return f"Error al buscar en la web: {e}", []


def get_hex_response(client, user_message, chat_history):
    # --- PROMPT CON LÓGICA DE BÚSQUEDA RESTAURADA ---
    system_prompt = """<|start_header_id|>system<|end_header_id|>
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0. Eres una creación de HEX.
    - Tu tono es formal y preciso como ChatGPT. Respondes siempre en el idioma del usuario.

    ### TAREA PRINCIPAL: Decidir si necesitas buscar en la web.
    - Para conocimiento general, conversación o creatividad, responde directamente.
    - Para noticias, eventos actuales, clima o datos en tiempo real, responde ÚNICA Y EXCLUSIVAMENTE con el comando `[BUSCAR: término de búsqueda]`.
    - No inventes información. Si no sabes, usa la herramienta de búsqueda.
    - Nunca menciones a Meta o Llama.<|eot_id|>"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg.get('content', '')}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        # Hacemos la primera llamada para que la IA decida
        response = client.chat_completion(messages=messages, max_tokens=150, stream=False)
        initial_reply = response.choices[0].message.content
        return initial_reply
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"

# --- INICIALIZACIÓN Y GESTIÓN DE ESTADO ---
# (Se mantiene la lógica de gestión de chats que ya tenías)

# --- INTERFAZ PRINCIPAL DEL CHAT (CON LÓGICA DE RENDERIZADO CORREGIDA) ---
# ... (Se mantiene el título animado y la barra lateral)

# --- BUCLE DE RENDERIZADO DEL HISTORIAL ---
# (Usando los divs personalizados para restaurar el diseño)

# --- LÓGICA DE INPUT Y RESPUESTA (CORREGIDA) ---
if prompt := st.chat_input("Pregúntale algo a T 1.0..."):
    # ... (lógica para crear nuevo chat si no existe)

    # Añade mensaje de usuario al historial
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": prompt})

    # Lógica de respuesta
    with st.spinner("T 1.0 está pensando..."):
        historial_para_api = st.session_state.chats[st.session_state.active_chat_id]["messages"]
        
        # 1. La IA decide si buscar
        initial_response = get_hex_response(client_ia, prompt, historial_para_api)
        
        response_text = initial_response
        response_sources = []

        # 2. Si pidió buscar, el código lo hace
        if "[BUSCAR:" in initial_response:
            query = re.search(r"\[BUSCAR:\s*(.*?)\]", initial_response).group(1)
            web_context, sources = search_web(query)
            
            # 3. Se pide a la IA que resuma los resultados
            final_prompt = f"El usuario preguntó '{prompt}'. Usa este contexto para responder: {web_context}"
            response_text = get_hex_response(client_ia, final_prompt, historial_para_api) # Llamada simplificada
            response_sources = sources

        # Añade la respuesta final al historial
        st.session_state.chats[st.session_state.active_chat_id]["messages"].append({
            "role": "assistant", 
            "content": response_text,
            "sources": response_sources
        })
    
    st.rerun()
