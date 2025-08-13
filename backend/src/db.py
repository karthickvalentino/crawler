import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from uuid import UUID

import psycopg2
from psycopg2.extras import Json, RealDictCursor, register_uuid
from src.models import JobCreate, JobUpdate

# Register UUID adapter
register_uuid()

DB_CONFIG = {
    "dbname": os.getenv("PGDATABASE", "test_db"),
    "user": os.getenv("PGUSER", "root"),
    "password": os.getenv("PGPASSWORD", "root"),
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", 5432),
}


def get_db_connection():
    """Create and return a new database connection."""
    return psycopg2.connect(**DB_CONFIG)


def insert_web_page(data: Dict[str, Any]):
    """Insert or update a web page in the database."""
    if not data:
        return
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            meta_tags = json.dumps([])
            try:
                meta_tags = json.dumps(list(data.get("meta_tags", []) or []))
            except Exception as e:
                print(f"Error serializing meta_tags: {e}")
                meta_tags = json.dumps([])

            cur.execute(
                """
                INSERT INTO web_pages (
                    url, domain, title, meta_description, meta_tags,
                    content, embedding, file_type, embedding_type, last_crawled
                ) VALUES (%s, %s, %s, %s, %s, %s, CAST(%s AS vector), %s, %s, NOW())
                ON CONFLICT (url) DO UPDATE SET
                    title = EXCLUDED.title,
                    meta_description = EXCLUDED.meta_description,
                    meta_tags = EXCLUDED.meta_tags,
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    file_type = EXCLUDED.file_type,
                    embedding_type = EXCLUDED.embedding_type,
                    last_crawled = NOW()
            """,
                (
                    data["url"],
                    urlparse(data["url"]).netloc,
                    data.get("title"),
                    data.get("meta_description"),
                    meta_tags,
                    data.get("content"),
                    data["embedding"],
                    data.get("file_type", "html"),
                    data.get("embedding_type", "text"),
                ),
            )


def search_web_pages(
    embedding: List[float], max_distance: float, top_k: int
) -> List[Dict[str, Any]]:
    """Search for web pages by embedding similarity."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT url, content, title, structured_data, (embedding <#> CAST(%s AS vector)) AS distance
                FROM web_pages
                WHERE (embedding <#> CAST(%s AS vector)) <= %s
                ORDER BY distance
                LIMIT %s
            """,
                (embedding, embedding, max_distance, top_k),
            )
            return cur.fetchall()


# New CRUD functions for Jobs


def create_job(job_in: JobCreate) -> Dict[str, Any]:
    """Create a new job in the database."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO jobs (parameters, status)
                VALUES (%s, 'pending')
                RETURNING id, parameters, status, created_at, updated_at
            """,
                (Json(job_in.parameters or {}),),
            )
            return cur.fetchone()


def get_job(job_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a single job by its ID."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
            return cur.fetchone()


def get_jobs(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Get a list of jobs with pagination."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset),
            )
            return cur.fetchall()


def update_job(job_id: UUID, job_up: JobUpdate) -> Optional[Dict[str, Any]]:
    """Update a job's status or result."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            update_fields = []
            params = []

            if job_up.status is not None:
                update_fields.append("status = %s")
                params.append(job_up.status)

            if job_up.result is not None:
                update_fields.append("result = %s")
                params.append(Json(job_up.result))

            if not update_fields:
                return get_job(job_id)

            update_fields.append("updated_at = NOW()")

            query = (
                f"UPDATE jobs SET {', '.join(update_fields)} WHERE id = %s RETURNING *"
            )

            params.append(job_id)
            cur.execute(query, tuple(params))

            return cur.fetchone()


def delete_job(job_id: UUID) -> bool:
    """Delete a job from the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
            return cur.rowcount > 0
