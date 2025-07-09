import streamlit as st
from huggingface_hub import InferenceClient
import random
from duckduckgo_search import DDGS

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

# --- LÓGICA DE LA IA ---
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
    """Realiza una búsqueda web priorizando resultados recientes."""
    print(f"🔎 Buscando en la web: '{query}'...")
    try:
        with DDGS() as ddgs:
            # --- MEJORA CLAVE: timelimit='m' busca en el último mes ---
            results = [{"snippet": r['body'], "url": r['href']} for r in ddgs.text(query, region='wt-wt', safesearch='off', timelimit='m', max_results=5)]
            if not results:
                return "No se encontraron resultados relevantes.", []
            context_text = "\n\n".join([f"Fuente: {r['snippet']}" for r in results])
            sources = [r for r in results]
            return context_text, sources
    except Exception:
        return "Error al intentar buscar en la web.", []

def get_hex_response(modelo_cliente, user_message, chat_history, web_context: str):
    """Genera una respuesta de la IA usando el contexto de la búsqueda."""
    system_prompt = f"""
    ### PERFIL
    Eres Tigre (T 1.0), un asistente de IA de la empresa HEX. Eres amigable y directo. Respondes siempre en el idioma del usuario.

    ### TAREA
    Tu única tarea es responder la "Pregunta del usuario" usando la "Información de la web" que te proporciono. Actúa como si TÚ hubieras encontrado esta información.

    ### INSTRUCCIONES CLAVE
    - Si la información de la web te permite responder sobre el **clima, la fecha, la hora o noticias actuales**, hazlo. Esa es tu principal función.
    - Si la información de la web no es relevante para la pregunta (por ejemplo, si el usuario solo dice "cómo estás"), ignora por completo la información de la web y responde de forma conversacional.
    - Nunca menciones el "contexto" o la "búsqueda".

    ### INFORMACIÓN DE LA WEB
    ---
    {web_context}
    ---
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history[-4:]) # Usamos un historial corto para mantener el contexto
    messages.append({"role": "user", "content": user_message})

    try:
        response = modelo_cliente.chat_completion(messages=messages, max_tokens=1024, stream=False)
        return response.choices[0].message.content
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"

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

# Diccionario para respuestas instantáneas
canned_responses = {
    "hola": ["¡Hola! Soy T 1.0. ¿En qué te puedo ayudar hoy?", "¡Hola! ¿Qué tal? Listo para asistirte."],
    "gracias": ["¡De nada! Es un placer ayudarte.", "Para eso estoy. ¿Necesitas algo más?"]
}

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        prompt_lower = prompt.lower().strip()
        
        # Filtro para saludos simples (CAMINO RÁPIDO)
        if prompt_lower in canned_responses:
            response_text = random.choice(canned_responses[prompt_lower])
            response_sources = []
            st.markdown(response_text)
        else:
            # Camino de búsqueda para todo lo demás
            with st.spinner("T 1.0 está buscando en la web..."):
                historial_para_api = st.session_state.messages[:-1]
                informacion_buscada, fuentes = search_duckduckgo(prompt)
                response_text = get_hex_response(client, prompt, historial_para_api, web_context=informacion_buscada)
                response_sources = fuentes
                
                st.markdown(response_text)
                if response_sources:
                    with st.expander("Fuentes Consultadas"):
                        for source in response_sources:
                            st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")
        
        assistant_message = {"role": "assistant", "content": response_text, "sources": response_sources}
        st.session_state.messages.append(assistant_message)
