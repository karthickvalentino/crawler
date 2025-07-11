import psycopg2
from psycopg2.extras import Json
import os
from urllib.parse import urlparse
import json
from psycopg2.extras import RealDictCursor


DB_CONFIG = {
    "dbname": os.getenv("PGDATABASE", "test_db"),
    "user": os.getenv("PGUSER", "root"),
    "password": os.getenv("PGPASSWORD", "root"),
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", 5432),
}

def insert_web_page(data):
    print("connecting to db")
    with psycopg2.connect(**DB_CONFIG) as conn:
        print("connected to db")
        with conn.cursor() as cur:
            print("cursor created")
            # print("embedding", data["embedding"])
            # print(data["meta_tags"])
            # print(type(data["meta_tags"]))
            data["meta_tags"] = json.dumps(list(data["meta_tags"]))
            if isinstance(data["meta_tags"], dict):
                data["meta_tags"] = Json(data["meta_tags"])

            print(data["meta_tags"])
            print(type(data["meta_tags"]))

            print(data)
            print(urlparse(data["url"]).netloc)
            try:
                cur.execute("""
                    INSERT INTO web_pages (
                        url, domain, title, meta_description, meta_tags,
                        content, embedding, last_crawled
                    ) VALUES (%s, %s, %s, %s, %s, %s, CAST(%s AS vector), NOW())
                        ON CONFLICT (url) DO UPDATE SET
                        title = EXCLUDED.title,
                        meta_description = EXCLUDED.meta_description,
                        meta_tags = EXCLUDED.meta_tags,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        last_crawled = NOW()
                """, (
                    data["url"],
                    urlparse(data["url"]).netloc,
                    data["title"],
                    data["meta_description"],
                    data["meta_tags"],
                    data["content"],
                    data["embedding"]
                ))
                conn.commit()
            except Exception as e:
                print(f"Error inserting data: {e}")
                conn.rollback()
            print("inserted")


# def insert_web_page(data):
#     with psycopg2.connect(**DB_CONFIG) as conn:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 INSERT INTO web_pages (
#                     url, domain, title, meta_description,
#                     meta_tags, content, embedding, last_crawled
#                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
#                 ON CONFLICT (url) DO UPDATE SET
#                     title = EXCLUDED.title,
#                     meta_description = EXCLUDED.meta_description,
#                     meta_tags = EXCLUDED.meta_tags,
#                     content = EXCLUDED.content,
#                     embedding = EXCLUDED.embedding,
#                     last_crawled = NOW()
#             """, (
#                 data["url"],
#                 urlparse(data["url"]).netloc,
#                 data["title"],
#                 data["meta_description"],
#                 Json(data["meta_tags"]),
#                 data["content"],
#                 data["embedding"]
#             ))

def search_web_pages(embedding, max_distance, top_k):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT url, content, title, (embedding <#> embedding) AS distance
                FROM web_pages
                WHERE embedding <#> CAST(%s AS vector) <= %s
                ORDER BY embedding <#> CAST(%s AS vector)
                LIMIT %s
            """, ( embedding, max_distance, embedding, top_k))
            return cur.fetchall()
        #  --WHERE embedding <#> CAST(%s AS vector) <= %s
        # embedding, max_distance,