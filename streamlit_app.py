# streamlit_app.py
import streamlit as st
from huggingface_hub import InferenceClient
import time, random, re, html
from datetime import datetime
import pytz
import requests, base64, io
from PIL import Image
import requests
from PIL import Image
from io import BytesIO

def generar_imagen_flux(prompt, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"inputs": prompt}
        response = requests.post(
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Error en la API: {response.status_code} - {response.text}")
        
        image = Image.open(BytesIO(response.content))
        return image
    
    except Exception as e:
        raise Exception(f"No se pudo generar: {e}")

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HEX T 1.0", page_icon="🤖", layout="wide")

# --- ESTILOS CSS & JS (copiar igual que antes) ---
st.markdown("""
<style> ... </style>
<script> ... </script>
""", unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---

@st.cache_resource
def get_client():
    try:
        return InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=st.secrets["HUGGINGFACE_API_TOKEN"])
    except Exception as e:
        st.error(f"Error al inicializar la API: {e}")
        return None

def generar_imagen_sd(prompt, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": prompt}
    resp = requests.post("https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev", headers=headers, json=payload)
    if resp.status_code != 200:
        raise Exception(f"Error {resp.status_code}: {resp.text}")
    data = resp.json()
    img_b64 = data.get("image_base64") or data.get("data", {}).get("image_base64")
    if not img_b64:
        raise Exception("No se encontró imagen_base64.")
    img = base64.b64decode(img_b64)
    return Image.open(io.BytesIO(img))

def get_current_datetime():
    now = datetime.now(pytz.utc)
    return f"Hoy es **{now.strftime('%A, %d de %B de %Y')}**."

def get_hex_response(client, user_message, chat_history):
    system_prompt = """<|start_header_id|>system<|end_header_id|>
    tu nombre legitimo es Tigre, Tu modelo es T 1.0, ... no menciones a cada rato quien te creo solo si te preguntan.<|eot_id|>"""
    messages = [{"role":"system","content":system_prompt}]
    for msg in chat_history:
        role = msg["role"]
        messages.append({"role":role,"content":msg["content"]})
    messages.append({"role":"user","content":user_message})
    try:
        full=""
        for chunk in client.chat_completion(messages=messages, max_tokens=2048, stream=True):
            full += chunk.choices[0].delta.content or ""
        return full
    except Exception as e:
        return f"Ha ocurrido un error con la API: {e}"

def generate_chat_name(p):
    return (p.split("\n")[0][:30] + "...") if len(p)>30 else p

# --- ESTADO & CLIENTE ---
client_ia = get_client()
st.session_state.setdefault("chats", {})
st.session_state.setdefault("active_chat_id", None)
st.session_state.setdefault("modo_generacion", "texto")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Conversaciones")
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.active_chat_id = None
        st.rerun()
    st.divider()
    for cid, info in st.session_state.chats.items():
        col1,col2 = st.columns([4,1])
        with col1:
            if st.button(info["name"], key=f"chat_{cid}"):
                st.session_state.active_chat_id = cid
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{cid}"):
                del st.session_state.chats[cid]
                if st.session_state.active_chat_id==cid:
                    st.session_state.active_chat_id=None
                st.rerun()
    st.divider()
    with st.expander("ℹ️ Acerca de HEX T 1.0"):
        st.markdown("**Proyecto:** HEX T 1.0\n**Misión:** Crear IA accesible.\n**Versión:** 1.0")

# --- ENCABEZADO & MODO ---
st.markdown("<div class='animated-title'>HEX</div><p class='subtitle'>T 1.0</p>", unsafe_allow_html=True)
modo = st.radio("Modo de entrada:", ["texto", "imagen"], index=0 if st.session_state.modo_generacion=="texto" else 1, key="modo_radio")
st.session_state.modo_generacion = modo

# --- GENERADOR DE IMÁGENES ---
if modo=="imagen":
    prompt_img = st.text_input("Prompt para imagen:")
    if st.button("Generar imagen"):
        if prompt_img:
            try:
                img = generar_imagen_flux(prompt_img, st.secrets["HUGGINGFACE_API_TOKEN"])
                st.image(img, caption="Imagen generada", use_container_width=True)
            except Exception as e:
                st.error(f"No se pudo generar: {e}")
        else:
            st.warning("Ingresá un prompt primero.")

# --- CHAT ---
chat_area = st.container()
active = st.session_state.active_chat_id
if active:
    msgs = st.session_state.chats[active]["messages"]
    with chat_area:
        for i,m in enumerate(msgs):
            cls = "user-bubble" if m["role"]=="user" else "bot-bubble"
            st.markdown(f"<div class='message-container {'user-container' if m['role']=='user' else 'bot-container'}'><div class='chat-bubble {cls}'>{m['content']}</div></div>", unsafe_allow_html=True)

if prompt:=st.chat_input("Escribí algo..."):
    if not st.session_state.active_chat_id:
        cid = str(time.time())
        st.session_state.active_chat_id = cid
        st.session_state.chats[cid]={"name":generate_chat_name(prompt),"messages":[]}
    st.session_state.chats[st.session_state.active_chat_id]["messages"].append({"role":"user","content":prompt})
    st.rerun()

if active and st.session_state.chats[active]["messages"]:
    last=st.session_state.chats[active]["messages"][-1]
    if last["role"]=="user":
        placeholder = st.empty()
        placeholder.markdown("<div class='bot-container'><div class='thinking-animation'>Pensando…</div></div>", unsafe_allow_html=True)
        if any(x in last["content"].lower() for x in ["qué fecha","que fecha","hoy es","dime la fecha"]):
            resp=get_current_datetime()
        else:
            resp=get_hex_response(client_ia, last["content"], st.session_state.chats[active]["messages"])
        placeholder.empty()
        st.session_state.chats[active]["messages"].append({"role":"assistant","content":resp})
        st.rerun()
