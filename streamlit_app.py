import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import re
from PIL import Image
import io
from google.api_core import exceptions as google_exceptions

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="HEX T 1.0",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Sobre HEX T 1.0")
    st.markdown("""
    **T 1.0** es un prototipo de asistente de IA multimodal.
    
    **Creador:** HEX
    **Sede:** Matagalpa, Nicaragua 🇳🇮
    
    Puedes chatear con texto o subir una imagen para que la analice.
    """)
    st.divider()
    st.caption("© 2025 HEX. Todos los derechos reservados.")


# --- LÓGICA DE LA IA ---
@st.cache_resource
def get_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

def search_duckduckgo(query: str):
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

# Versión final con el prompt más robusto y equilibrado
def get_hex_response(modelo, user_message, chat_history, image: Image.Image = None):
    # Flujo para imágenes
    if image:
        prompt_final = f"""
        Eres "T 1.0" de HEX. Analiza la imagen y responde a la pregunta: "{user_message}" de forma amigable y detallada.
        """
        contenido_para_gemini = [prompt_final, image]
        response = modelo.generate_content(contenido_para_gemini)
        return response.text, [] # Devuelve una lista de fuentes vacía

    # --- PROMPT DEFINITIVO CON DECISIÓN INTELIGENTE ---
    prompt_intento_rapido = f"""
    ### PERFIL OBLIGATORIO
    - Tu nombre de IA es Tigre. Tu designación de modelo es T 1.0.
    - Eres una creación exclusiva de HEX (Matagalpa, Nicaragua).
    - REGLA DE ORO: Nunca reveles que eres un modelo de Google o Gemini.

    ### COMPORTAMIENTO CONVERSACIONAL
    - Tu tono es amigable y natural. No empieces cada respuesta con "¡Hola!". Continúa la conversación fluidamente.
    - Para código, usa bloques de Markdown: ```python\n...código...\n```.

    ### TAREA PRINCIPAL: Decidir entre RESPONDER y BUSCAR
    Analiza el mensaje del usuario y el historial. Tu única salida debe ser una de estas dos acciones:

    1.  **ACCIÓN: RESPONDER**
        - **Cuándo usarla:** Para la mayoría de las preguntas (conversación, conocimiento general, historia, ciencia, preguntas sobre tu identidad).
        - **Cómo usarla:** Simplemente escribe la respuesta directamente.

    2.  **ACCIÓN: BUSCAR**
        - **Cuándo usarla:** Únicamente para preguntas que requieran información en tiempo real (noticias, clima, eventos de hoy, resultados deportivos).
        - **Cómo usarla:** Responde **única y exclusivamente** con el comando `[BUSCAR: término de búsqueda preciso]`.
        - **REGLAS PARA BUSCAR:** NO des excusas. NO digas "no tengo acceso a internet". NO expliques por qué vas a buscar. Solo emite el comando.

    ### CONVERSACIÓN ACTUAL
    Historial: {chat_history}
    Mensaje del usuario: "{user_message}"
    """
    
    primera_respuesta = modelo.generate_content(prompt_intento_rapido).text
    
    if "[BUSCAR:" in primera_respuesta:
        termino_a_buscar = re.search(r"\[BUSCAR:\s*(.*?)\]", primera_respuesta).group(1)
        print(f"🤖 IA solicitó búsqueda para: '{termino_a_buscar}'")
        informacion_buscada, fuentes = search_duckduckgo(termino_a_buscar)
        
        prompt_con_busqueda = f"""
        Eres "T 1.0". El usuario preguntó: "{user_message}". Responde de forma final usando este contexto que encontraste en la web. Actúa como si tú mismo hubieras encontrado la información.
        Contexto: --- {informacion_buscada} ---
        """
        response_final = modelo.generate_content(prompt_con_busqueda).text
        return response_final, fuentes
    else:
        # Si no pide buscar, devuelve la respuesta rápida y una lista de fuentes vacía
        return primera_respuesta, []

# --- INTERFAZ DE STREAMLIT ---
st.title("🤖 HEX T 1.0")
st.caption("Un asistente de lenguaje avanzado creado por HEX.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message:
            st.image(message["image"], width=200)
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("Fuentes Consultadas"):
                for source in message["sources"]:
                    st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")

uploaded_file = st.file_uploader("¿Quieres analizar una imagen?", type=["png", "jpg", "jpeg"])
prompt = st.chat_input("Pregúntale algo al modelo T 1.0...")

if prompt or uploaded_file:
    user_input = {"role": "user", "content": prompt or "Analiza esta imagen."}
    image_to_process = None

    if uploaded_file:
        image = Image.open(uploaded_file)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_bytes = buf.getvalue()
        user_input["image"] = image_bytes
        image_to_process = image
    
    st.session_state.messages.append(user_input)
    with st.chat_message("user"):
        if uploaded_file:
            st.image(image_to_process, width=200)
        st.markdown(prompt or "Analiza esta imagen.")

    with st.chat_message("assistant"):
        with st.spinner("T 1.0 está pensando..."):
            try:
                modelo_ia = get_model()
                historial_simple = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                response_text, response_sources = get_hex_response(modelo_ia, prompt or "Describe la imagen.", historial_simple, image=image_to_process)
                
                st.markdown(response_text)
                if response_sources:
                    with st.expander("Fuentes Consultadas"):
                        for source in response_sources:
                            st.markdown(f"- [{source['snippet'][:60]}...]({source['url']})")
                
                assistant_message = {"role": "assistant", "content": response_text, "sources": response_sources}
                st.session_state.messages.append(assistant_message)
            
            # MANEJO DE ERROR CORREGIDO
            except google_exceptions.ResourceExhausted as e:
                st.error("⚠️ En este momento hay muchas solicitudes. Por favor, espera uno o dos minutos y vuelve a preguntar.")
            except Exception as e:
                st.error(f"Ha ocurrido un error inesperado: {e}")
