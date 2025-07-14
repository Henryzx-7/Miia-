# image_generator.py
from huggingface_hub import InferenceClient
from PIL import Image
import io
import streamlit as st

# Usamos un modelo popular y rápido para generar imágenes
IMAGE_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"

def generate_image(prompt: str, api_token: str) -> Image.Image:
    """
    Genera una imagen a partir de un prompt de texto.
    """
    print(f"🎨 Generando imagen para: '{prompt}'")
    try:
        # Creamos un cliente de API específico para esta tarea
        client = InferenceClient(model=IMAGE_MODEL_ID, token=api_token)

        # La función para generar imágenes es 'text_to_image'
        image_bytes = client.text_to_image(prompt,
                                           height=512,
                                           width=512,
                                           num_inference_steps=25,
                                           guidance_scale=7.0)

        # Convertimos los bytes de la imagen en un objeto de imagen que Streamlit puede mostrar
        image = Image.open(io.BytesIO(image_bytes))
        return image

    except Exception as e:
        # Si el modelo está ocupado o hay un error, lo notificamos
        st.error(f"Error al generar la imagen: El modelo puede estar ocupado. Inténtalo de nuevo. ({e})")
        return None
