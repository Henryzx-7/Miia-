import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image
import io
import random
from duckduckgo_search import DDGS
import re

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

# --- LÓGICA DE LA IA ---
try:
    client = InferenceClient(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        token=st.secrets["HUGGINGFACE_API_TOKEN"]
    )
except Exception as e:
    st.error(f"No se pudo inicializar el cliente de la API: {e}")
    st.stop()

def search_duckduckgo(query: str):
    """Realiza una búsqueda web y devuelve contexto y fuentes."""
    print(f"🔎 Buscando en la web: '{query}'...")
    try:
        with DDGS() as ddgs:
            results = [{"snippet": r['body'], "url": r['href']} for r in ddgs.text(query, region='wt-wt', safesearch='off', timelimit='m', max_results=3)]
            if not results:
                return "No se encontraron resultados relevantes.", []
            context_text = "\n\n".join([f"Fuente: {r['snippet']}" for r in results])
            sources = [r for r in results]
            return context_text, sources
    except Exception:
        return "Error al intentar buscar en la web.", []

@st.cache_data(show_spinner=False)
def get_hex_response(_user_message, _chat_history):
    """Genera una respuesta, decidiendo si buscar en la web primero."""
    system_prompt = """
    <|start_header_id|>system<|end_header_id|>
    Eres Tigre (T 1.0), un asistente de IA de HEX. Tu tono es amigable y profesional. Respondes siempre en el idioma del usuario. Tu principal limitación es que NO tienes acceso a internet. Para noticias, eventos actuales, o clima, responde ÚNICA Y EXCLUSIVAMENTE con el comando `[BUSCAR: término de búsqueda preciso]`. Nunca menciones a Meta o Llama.<|eot_id|>
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in _chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"})
    messages.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{_user_message}<|eot_id|>"})

    try:
        response = client.chat_completion(messages=messages, max_tokens=150, stream=False)
        initial_reply = response.choices[0].message.content

        if "[BUSCAR:" in initial_reply:
            query = re.search(r"\[BUSCAR:\s*(.*?)\]", initial_reply).group(1)
            search_results, sources = search_duckduckgo(query)
            
            final_prompt = f"""<|start_header_id|>system<|end_header_id|>
            Eres Tigre (T 1.0). Responde la pregunta del usuario ("{_user_message}") usando la siguiente información que encontraste en la web. Sé conciso y amigable.<|eot_id|>
            <|start_header_id|>user<|end_header_id|>
            Información de la web: {search_results}<|eot_id|>"""
            
            final_messages = [{"role": "user", "content": final_prompt}]
            final_response = client.chat_completion(messages=final_messages, max_tokens=1024, stream=False)
            return final_response.choices[0].message.content, sources
        else:
            return initial_reply, []
            
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}", []

# --- INTERFAZ DE STREAMLIT ---
st.title("HEX T 1.0")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial con los componentes nativos de Streamlit
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Fuentes Consultadas"):
                for source in message["sources"]:
                    st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")

# Input del usuario
prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            # Convertimos el historial a una tupla para que sea cacheable
            historial_para_cache = tuple(
                (k, tuple(v.items())) if isinstance(v, dict) else (k, v)
                for item in st.session_state.messages[:-1]
                for k, v in item.items()
            )
            
            response_text, response_sources = get_hex_response(prompt, historial_para_cache)
            
            st.markdown(response_text)
            if response_sources:
                with st.expander("Fuentes Consultadas"):
                    for source in response_sources:
                        st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")
            
            assistant_message = {"role": "assistant", "content": response_text, "sources": response_sources}
            st.session_state.messages.append(assistant_message)
