import re
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from src.embeddings import create_embedding_with_ollama, truncate_or_pad_vector, normalize
from src.db import search_web_pages, DB_CONFIG

def get_dashboard_analytics():
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(DISTINCT domain) as total_domains FROM web_pages")
            total_domains = cur.fetchone()['total_domains']
            
            cur.execute("SELECT COUNT(*) as total_urls FROM web_pages")
            total_urls = cur.fetchone()['total_urls']
            
            cur.execute("SELECT COUNT(*) as running_crawlers FROM jobs WHERE status = 'running'")
            running_crawlers = cur.fetchone()['running_crawlers']
            
            cur.execute("SELECT COUNT(*) as jobs_completed FROM jobs WHERE status = 'completed'")
            jobs_completed = cur.fetchone()['jobs_completed']
            
            return {
                "total_domains": total_domains,
                "total_urls": total_urls,
                "running_crawlers": running_crawlers,
                "jobs_completed": jobs_completed,
            }

def get_web_pages(limit: int = 10, offset: int = 0, sort_by: str = "last_crawled", sort_order: str = "desc", query: str = None):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            sql_query = "SELECT id, url, domain, title, last_crawled FROM web_pages"
            count_query = "SELECT COUNT(*) FROM web_pages"
            params = []
            
            if query:
                sql_query += " WHERE to_tsvector('english', title || ' ' || domain || ' ' || url) @@ to_tsquery('english', %s)"
                count_query += " WHERE to_tsvector('english', title || ' ' || domain || ' ' || url) @@ to_tsquery('english', %s)"
                params.append(query)

            cur.execute(count_query, params)
            total = cur.fetchone()['count']
            
            sql_query += f" ORDER BY {sort_by} {sort_order} LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(sql_query, params)
            web_pages = cur.fetchall()
            
            return {"total": total, "data": web_pages}

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
