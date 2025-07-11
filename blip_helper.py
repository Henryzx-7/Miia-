# blip_helper.py
import requests
import streamlit as st

def get_image_caption(image_bytes: bytes, api_token: str) -> str:
    """
    Toma los bytes de una imagen y devuelve una descripción usando el modelo BLIP.
    """
    API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
    headers = {"Authorization": f"Bearer {api_token}"}
    
    try:
        response = requests.post(API_URL, headers=headers, data=image_bytes)
        if response.status_code == 200:
            # La respuesta es una lista de diccionarios, tomamos el primer resultado.
            caption = response.json()[0].get('generated_text', 'No se pudo generar una descripción.')
            return caption
        else:
            # Intentamos dar un error más específico si es posible
            error_info = response.json().get('error', response.text)
            st.error(f"Error al analizar la imagen (Código {response.status_code}): {error_info}")
            return None
    except Exception as e:
        st.error(f"Ocurrió un error de conexión al analizar la imagen: {e}")
        return None
