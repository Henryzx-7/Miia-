def generar_imagen_sd(prompt, token):
    import requests
    import io
    from PIL import Image
    import base64

    url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    payload = {
        "inputs": prompt,
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        image_bytes = response.content
        try:
            return Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError("No se pudo decodificar la imagen: " + str(e))
    else:
        raise ValueError(f"No se pudo generar: {response.text}")
