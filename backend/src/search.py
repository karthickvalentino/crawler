import re
import numpy as np
from src.embeddings import create_embedding_with_ollama, truncate_or_pad_vector, normalize
from src.db import search_web_pages

def search(query, top_k):
    print("Searching for:", query)
    embedding = create_embedding_with_ollama(query)
    print(f"Embedding shape: {np.array(embedding).shape}")
    embedding = normalize(embedding)
    embedding = truncate_or_pad_vector(embedding, dims=1024)
    print(f"Reduced embedding shape: {np.array(embedding).shape}")
    threshold = 0.95
    max_distance = 1 - threshold
    # print(f"Embedding: {embedding}")
    output = []
    # return search_web_pages(embedding, max_distance, top_k)
    results = search_web_pages(embedding, max_distance, top_k)
    for row in results:
        snippet = extract_snippet(row["content"], query)
        output.append({
            "url": row["url"],
            "title": row["title"],
            "snippet": snippet,
            "distance": row["distance"]
        })
    return output

def extract_snippet(content: str, query: str, max_len: int = 200):
    # Break query into terms
    terms = re.findall(r'\w+', query.lower())
    content_lower = content.lower()

    # Try to find where any term appears
    for term in terms:
        idx = content_lower.find(term)
        if idx != -1:
            start = max(0, idx - max_len // 2)
            end = min(len(content), idx + max_len // 2)
            snippet = content[start:end].strip()
            return "... " + snippet + " ..."
    
    # Fallback: return beginning of content
    return content[:max_len].strip() + "..."
