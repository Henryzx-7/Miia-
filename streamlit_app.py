import streamlit as st
from PIL import Image
import io
from huggingface_hub import InferenceClient
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
    st.caption("© 2025 HEX. Todos los derechos reservados.")

# --- LÓGICA DE LA IA CON HUGGING FACE Y BÚSQUEDA ---
try:
    if "HUGGINGFACE_API_TOKEN" not in st.secrets:
        st.error("No se encontró la clave de Hugging Face. Asegúrate de añadirla a los 'Secrets'.")
        st.stop()
    
    client = InferenceClient(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        token=st.secrets["HUGGINGFACE_API_TOKEN"]
    )
except Exception as e:
    st.error(f"No se pudo inicializar el cliente de la API: {e}")
    st.stop()

def search_duckduckgo(query: str):
    """Realiza una búsqueda web y devuelve contexto y una lista de fuentes."""
    print(f"🔎 Buscando en la web: '{query}'...")
    try:
        with DDGS() as ddgs:
            results = [{"snippet": r['body'], "url": r['href']} for r in ddgs.text(query, max_results=4)]
            if not results:
                return "No se encontraron resultados.", []
            context_text = "\n".join([r['snippet'] for r in results])
            sources = [r for r in results]
            return context_text, sources
    except Exception:
        return "Error al buscar en la web.", []

def get_hex_response(user_message, chat_history):
    """
    Genera una respuesta, decidiendo si necesita buscar en la web primero.
    Ahora devuelve tanto el texto de la respuesta como las fuentes.
    """
    system_prompt = """<|start_header_id|>system<|end_header_id|>

Eres Tigre (T 1.0), un asistente de IA de HEX. Eres amigable y directo. Respondes en el mismo idioma que el usuario.
Tu tarea es decidir si puedes responder directamente o si necesitas buscar en la web.
Para noticias, eventos actuales o clima, responde ÚNICA Y EXCLUSIVAMENTE con el comando `[BUSCAR: término de búsqueda]`.
Para todo lo demás, responde directamente. Nunca menciones a Meta o Llama.<|eot_id|>"""
    
    messages_for_decision = [{"role": "system", "content": system_prompt}]
    messages_for_decision.extend(chat_history)
    messages_for_decision.append({"role": "user", "content": f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"})

    try:
        # Primera llamada para ver si necesita buscar
        initial_response = client.text_generation(str(messages_for_decision), max_new_tokens=100, stream=False)
        
        # Si la IA pide buscar...
        if "[BUSCAR:" in initial_response:
            query = re.search(r"\[BUSCAR:\s*(.*?)\]", initial_response).group(1)
            search_results, sources = search_duckduckgo(query)
            
            # Segunda llamada con el contexto de la búsqueda
            final_prompt = f"""<|start_header_id|>system<|end_header_id|>

            Eres Tigre (T 1.0). Responde la pregunta del usuario usando la siguiente información que encontraste en la web. Sé conciso y amigable.<|eot_id|>
            <|start_header_id|>user<|end_header_id|>

            Información de la web: {search_results}
            Pregunta del usuario: {user_message}<|eot_id|>"""
            
            final_response = client.text_generation(final_prompt, max_new_tokens=1024, stream=False)
            return final_response, sources
        else:
            # Si no necesita buscar, devuelve la primera respuesta y ninguna fuente
            return initial_response, []
            
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}", []

# --- INTERFAZ DE STREAMLIT ---
st.markdown("<h1 style='text-align: center; font-size: 4em; font-weight: bold;'>HEX</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; margin-top: -25px;'>T 1.0</h3>", unsafe_allow_html=True)
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Mostramos las fuentes si existen en el mensaje del asistente
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("Fuentes Consultadas"):
                for source in message["sources"]:
                    st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")

prompt = st.chat_input("Pregúntale algo a T 1.0...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            historial_para_api = st.session_state.messages[:-1]
            # La función ahora devuelve dos valores: el texto y las fuentes
            response_text, response_sources = get_hex_response(prompt, historial_para_api)
            
            st.markdown(response_text)
            # Mostramos las fuentes DEBAJO de la respuesta nueva
            if response_sources:
                with st.expander("Fuentes Consultadas"):
                    for source in response_sources:
                        st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")
            
            # Guardamos la respuesta Y las fuentes en el historial
            assistant_message = {"role": "assistant", "content": response_text, "sources": response_sources}
            st.session_state.messages.append(assistant_message)
