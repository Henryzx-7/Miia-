import streamlit as st
from huggingface_hub import InferenceClient
import time
import json
import re
from web_search import search_web  # Importamos nuestra nueva función
from utils import get_formatted_date, generate_chat_name # Importamos nuestras nuevas utilidades

# --- CONFIGURACIÓN Y ESTILOS (SIN CAMBIOS) ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")
# Aquí va tu bloque de st.markdown(<style>...</style>) completo...
st.markdown("""<style>...</style>""", unsafe_allow_html=True) # <-- Asegúrate de tener tu CSS completo aquí

# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_client():
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"Error al inicializar la API: {e}")
        return None

def get_hex_response(client, user_message, chat_history):
    system_prompt = """<|start_header_id|>system<|end_header_id|>
    ### Perfil
    Eres Tigre (T 1.0), un asistente de IA experto de HEX. Tu tono es profesional y preciso. Tu idioma de respuesta se adapta al del usuario.

    ### Herramientas
    Tienes una herramienta para buscar en la web: `web_search(query: str)`.

    ### Tarea
    Analiza la pregunta del usuario.
    1. Si la pregunta se puede responder con tu conocimiento general (ej. 'explícame la gravedad'), responde directamente.
    2. Si la pregunta requiere información actual (noticias, clima, eventos recientes, 'qué pasó hoy'), DEBES usar tu herramienta. Para hacerlo, responde ÚNICAMENTE con un objeto JSON con el siguiente formato: `{"tool": "web_search", "query": "término de búsqueda preciso"}`.
    3. NO inventes información. Si no sabes, usa la herramienta de búsqueda.<|eot_id|>"""
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})
    
    try:
        response = client.chat_completion(messages=messages, max_tokens=1024, stream=False)
        return response.choices[0].message.content
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"

# --- INICIALIZACIÓN Y SIDEBAR (SIN CAMBIOS) ---
client_ia = get_client()
# ... El código del sidebar y la gestión de estado se mantiene igual ...

# --- INTERFAZ PRINCIPAL DEL CHAT ---
st.markdown("<div class='animated-title'>HEX</div><p class='subtitle'>T 1.0</p>", unsafe_allow_html=True)
# ... El código para mostrar el historial se mantiene igual ...

# Input del usuario
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    # Lógica para crear un nuevo chat si es necesario
    if st.session_state.active_chat_id is None:
        new_chat_id = str(time.time())
        st.session_state.active_chat_id = new_chat_id
        st.session_state.chats[new_chat_id] = {"name": generate_chat_name(prompt), "messages": []}
    
    active_chat_messages = st.session_state.chats[st.session_state.active_chat_id]["messages"]
    active_chat_messages.append({"role": "user", "content": prompt})

    # --- LÓGICA DE RESPUESTA MEJORADA ---
    prompt_lower = prompt.lower().strip()
    
    # Nivel 1: Filtro de Fecha (usa nuestro módulo de utilidades)
    if any(s in prompt_lower for s in ["fecha", "día es hoy", "hora es", "a cómo estamos"]):
        response_text = get_formatted_date(prompt_lower)
        active_chat_messages.append({"role": "assistant", "content": response_text})
        st.rerun()
    
    # Nivel 2: Llamada a la IA para todo lo demás
    else:
        if client_ia:
            with st.spinner("T 1.0 está pensando..."):
                historial_para_api = active_chat_messages
                
                # Primera llamada a la IA para que decida
                initial_response = get_hex_response(client_ia, prompt, historial_para_api)

                # Verificamos si la IA pidió usar la herramienta de búsqueda
                try:
                    tool_call = json.loads(initial_response)
                    if tool_call.get("tool") == "web_search":
                        with st.spinner(f"Buscando en la web sobre: '{tool_call['query']}'..."):
                            context, sources = search_web(tool_call['query'])
                            # Segunda llamada a la IA con el contexto
                            final_prompt = f"El usuario preguntó: '{prompt}'. Usando la siguiente información de la web, formula una respuesta completa y útil, citando tus fuentes: {context}"
                            response_text = get_hex_response(client_ia, final_prompt, historial_para_api)
                            # Aquí podríamos añadir las fuentes a la respuesta
                    else:
                        response_text = initial_response # No era una llamada a la herramienta
                except (json.JSONDecodeError, TypeError):
                    # Si no es un JSON, es una respuesta directa
                    response_text = initial_response

                active_chat_messages.append({"role": "assistant", "content": response_text})
        else:
            active_chat_messages.append({"role": "assistant", "content": "El cliente de la API no está disponible."})
        
        st.rerun()
