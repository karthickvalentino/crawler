import requests
import  numpy as np
from numpy import random, dot, linalg
from sklearn.decomposition import TruncatedSVD
from src.config import settings

def create_embedding_with_ollama(text, model="llama3.2:latest"):
    response = requests.post(
        settings.ollama_url,
        json={"model": model, "prompt": text}
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