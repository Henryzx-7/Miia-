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
    """
    # Formateo del historial para la API
    messages = [
        {
            "role": "system",
            "content": """
            ### PERFIL OBLIGATORIO
            - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0. Eres una creación de HEX.
            - Tu idioma principal y preferido es el español. Responde siempre en español a menos que el usuario escriba en inglés.

            ### TAREA PRINCIPAL: Decidir si necesitas buscar en la web.
            - Para conocimiento general, conversación o creatividad, responde directamente.
            - Para noticias, eventos actuales, clima o datos específicos en tiempo real, responde ÚNICA Y EXCLUSIVAMENTE con el comando `[BUSCAR: término de búsqueda]`.

            ### EJEMPLO
            - Usuario: "¿Cuál es el clima en Managua?" -> Tu respuesta: `[BUSCAR: clima actual en Managua]`
            """
        }
    ]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_message})

    try:
        # Primera llamada para ver si necesita buscar (usando chat_completion)
        response = client.chat_completion(messages=messages, max_tokens=150, stream=False)
        initial_reply = response.choices[0].message.content

        # Si la IA pide buscar...
        if "[BUSCAR:" in initial_reply:
            query = re.search(r"\[BUSCAR:\s*(.*?)\]", initial_reply).group(1)
            search_results, sources = search_duckduckgo(query)
            
            # Segunda llamada con el contexto de la búsqueda
            final_prompt = f"""
            Eres Tigre (T 1.0). El usuario preguntó "{user_message}". Responde a su pregunta de forma amigable y en español, usando la siguiente información que encontraste en la web:
            
            Contexto: {search_results}
            """
            final_messages = [{"role": "user", "content": final_prompt}]
            final_response = client.chat_completion(messages=final_messages, max_tokens=1024, stream=False)
            return final_response.choices[0].message.content, sources
        else:
            # Si no necesita buscar, devuelve la primera respuesta
            return initial_reply, []
            
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
            response_text, response_sources = get_hex_response(prompt, historial_para_api)
            
            st.markdown(response_text)
            if response_sources:
                with st.expander("Fuentes Consultadas"):
                    for source in response_sources:
                        st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")
            
            assistant_message = {"role": "assistant", "content": response_text, "sources": response_sources}
            st.session_state.messages.append(assistant_message)
