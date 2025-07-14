# imagegen_flux.py
import requests
from PIL import Image
from io import BytesIO

def generar_imagen_flux(prompt, api_token):
    url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"inputs": prompt}

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        image_bytes = BytesIO(response.content)
        try:
            return Image.open(image_bytes)
        except Exception as e:
            raise ValueError("No se pudo abrir la imagen. El modelo no respondió una imagen válida.")
    else:
        raise ValueError(f"Error de la API: {response.status_code} – {response.text}")
