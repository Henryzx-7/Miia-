def generar_imagen_flux(prompt, token):
    import requests, base64, io
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
        # La respuesta es una imagen como base64
        result = response.json()
        image_base64 = result.get("image_base64") or result.get("data", {}).get("image_base64")
        if not image_base64:
            raise Exception("No se encontró imagen_base64 en la respuesta.")
        
        image_data = base64.b64decode(image_base64)
        return Image.open(io.BytesIO(image_data))
    except Exception as e:
        raise Exception(f"Error al procesar la imagen: {e}")
