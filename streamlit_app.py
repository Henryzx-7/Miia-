import streamlit as st
from huggingface_hub import InferenceClient
import time
import random
from datetime import datetime
import pytz
import re
from duckduckgo_search import DDGS

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# Carga el CSS desde el archivo externo
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")


# --- LÓGICA DE LA IA Y FUNCIONES ---
@st.cache_resource
def get_client():
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"Error al inicializar la API: {e}")
        return None

def search_web_for_context(query: str):
    """Realiza una búsqueda y devuelve contexto y fuentes."""
    print(f"🔎 Buscando: '{query}'...")
    try:
        with DDGS() as ddgs:
            results = [{"snippet": r['body'], "url": r['href']} for r in ddgs.text(query, max_results=3)]
            if not results: return "No se encontraron resultados.", []
            context_text = "\n\n".join([f"Fuente: {r['snippet']}" for r in results])
            return context_text, results
    except Exception:
        return "Error al buscar.", []

def get_hex_response(client, user_message, chat_history, web_context=None):
    """Genera una respuesta, usando contexto web si se proporciona."""
    if web_context:
        # Prompt para cuando SÍ hay búsqueda web
        system_prompt = f"""<|start_header_id|>system<|end_header_id|>
        Eres Tigre (T 1.0), un asistente de IA. Tu tarea es responder la pregunta del usuario usando la información de la web que te proporciono. Actúa como si tú hubieras encontrado la información. Sé conciso y responde en español.
        
        ### INFORMACIÓN DE LA WEB
        {web_context}
        <|eot_id|>"""
    else:
        # Prompt para conversaciones normales
        system_prompt = """<|start_header_id|>system<|end_header_id|>
        Eres Tigre (T 1.0), un asistente de IA de HEX. Tu tono es amigable y profesional. Respondes en español. No tienes acceso a internet. Si te piden buscar, debes usar tu herramienta `[BUSCAR: tema]`.<|eot_id|>"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        response = client.chat_completion(messages=messages, max_tokens=1500, stream=False)
        return response.choices[0].message.content
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"

# ... (El resto de tu código para sidebar, historial, etc. se mantiene igual)
# Asegúrate de reemplazar la sección de Lógica de Respuesta en el `if prompt:`

# --- LÓGICA DE RESPUESTA ---
# if prompt:
#     # ...
#     with st.chat_message("assistant"):
#         with st.spinner("T 1.0 está pensando..."):
#             historial_para_api = st.session_state.chats[st.session_state.active_chat_id]["messages"]
#             
#             # Primera llamada para decidir si buscar
#             initial_response_text = get_hex_response(client_ia, prompt, historial_para_api)
#             
#             response_text = initial_response_text
#             response_sources = []
#
#             # Si la IA pide buscar
#             if "[BUSCAR:" in initial_response_text:
#                 query = re.search(r"\[BUSCAR:\s*(.*?)\]", initial_response_text).group(1)
#                 web_context, sources = search_web_for_context(query)
#                 # Segunda llamada con el contexto
#                 response_text = get_hex_response(client_ia, prompt, historial_para_api, web_context=web_context)
#                 response_sources = sources
#
#             st.markdown(response_text)
#             if response_sources:
#                 with st.expander("Fuentes Consultadas"):
#                     for source in response_sources:
#                         st.markdown(f"- {source['url']}")
#
#     st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": response_text, "sources": response_sources})
#     st.rerun()
