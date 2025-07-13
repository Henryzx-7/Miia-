# blip_helper.py
import requests
import streamlit as st

def get_image_caption(image_bytes: bytes, api_token: str) -> str:
    """
    Toma los bytes de una imagen y devuelve una descripción usando el modelo BLIP.
    """
    API_URL = "https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning"
    headers = {"Authorization": f"Bearer {api_token}"}
    
    try:
        response = requests.post(API_URL, headers=headers, data=image_bytes)
        response.raise_for_status() # Lanza una excepción para errores HTTP (como 404, 503, etc.)

        # --- CORRECCIÓN IMPORTANTE ---
        # Verificamos si la respuesta es un JSON válido antes de procesarla
        try:
            json_response = response.json()
            if isinstance(json_response, list) and json_response:
                caption = json_response[0].get('generated_text', 'No se pudo generar una descripción.')
                return caption
            else:
                # El JSON es válido pero no tiene el formato esperado
                st.error(f"La respuesta de la API de imágenes no tuvo el formato esperado: {json_response}")
                return None
        except requests.exceptions.JSONDecodeError:
            # Si la respuesta no es JSON (ej. una página de error de HTML), lo indicamos
            st.error(f"Error al analizar la imagen: El modelo puede estar sobrecargado. Respuesta recibida: {response.text[:100]}...")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Ocurrió un error de conexión al analizar la imagen: {e}")
        return None
