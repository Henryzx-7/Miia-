# imagegen_flux.py

import requests
from PIL import Image
from io import BytesIO

def generar_imagen_flux(prompt: str, api_token: str):
    """
    Usa el modelo FLUX.1-dev para generar una imagen desde texto.
    """
    api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"inputs": prompt}

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        image_bytes = response.content
        image = Image.open(BytesIO(image_bytes))
        return image
    else:
        raise Exception(f"Error al generar imagen: {response.status_code} - {response.text}")
