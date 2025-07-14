def generar_imagen_flux(prompt, token):
    import requests
    import base64
    import io
    from PIL import Image

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": prompt}
    
    response = requests.post(
        "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev",
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")

    try:
        result = response.json()
        image_base64 = result.get("image_base64", None)
        if image_base64:
            image_data = base64.b64decode(image_base64)
            return Image.open(io.BytesIO(image_data))
        else:
            raise Exception("No se encontró imagen_base64 en la respuesta.")
    except Exception as e:
        raise Exception(f"Error al procesar la imagen: {e}")
