import requests
import numpy as np
from numpy import random, dot, linalg
from sklearn.decomposition import TruncatedSVD
from src.config import settings
import base64
from io import BytesIO
from PIL import Image

def create_embedding_with_ollama(text, model="llama3.2:latest"):
    response = requests.post(
        settings.ollama_url,
        json={"model": model, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]

def create_multimodal_embedding_with_ollama(image_url: str, model="llava:latest"):
    """
    Generates a multimodal embedding for an image using Ollama.
    """
    response = requests.get(image_url)
    response.raise_for_status()
    
    # Open the image and convert to RGB
    img = Image.open(BytesIO(response.content)).convert("RGB")
    
    # Convert image to base64
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # Generate embedding
    response = requests.post(
        settings.ollama_url,
        json={
            "model": model,
            "prompt": "Describe this image.", # A generic prompt is often needed
            "images": [img_base64]
        }
    )
    response.raise_for_status()
    return response.json()["embedding"]

def pad_vector(vector, dims=1024):
    if len(vector) > dims:
        return vector[:dims]
    return vector + [0.0] * (dims - len(vector))

def truncate_or_pad_vector(vector, dims=1024):
    if len(vector) >= dims:
        return vector[:dims]
    else:
        return vector + [0.0] * (dims - len(vector))

def reduce_vector(vector, dims=1024):
    svd = TruncatedSVD(n_components=dims, random_state=42)
    reduced = svd.fit_transform([vector])
    return reduced.tolist()

def normalize(embedding: list[float]) -> list[float]:
    norm = np.linalg.norm(embedding)
    print(norm)
    if norm == 0:
        return embedding  # avoid division by zero
    print(dot(norm, norm))
    return (np.array(embedding) / norm).tolist()
