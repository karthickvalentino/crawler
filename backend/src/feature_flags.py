import logging
from functools import lru_cache
from typing import Dict

from src.db import DB_CONFIG
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# In-memory cache with a small size to avoid frequent DB calls
@lru_cache(maxsize=32)
def get_all_flags() -> Dict[str, bool]:
    """
    Fetches all feature flags from the database.
    Results are cached in memory.
    """
    logger.info("Fetching feature flags from the database.")
    flags = {}
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT name, is_enabled FROM feature_flags")
                for row in cur.fetchall():
                    flags[row['name']] = row['is_enabled']
    except Exception as e:
        logger.error(f"Error fetching feature flags: {e}", exc_info=True)
        # In case of DB error, return an empty dict to avoid breaking the app
        return {}
    return flags

def is_feature_enabled(feature_name: str) -> bool:
    """
    Checks if a specific feature is enabled.
    Uses the cached get_all_flags function.
    """
    flags = get_all_flags()
    return flags.get(feature_name, False)

def clear_flag_cache():
    """
    Clears the in-memory cache for feature flags.
    """
    get_all_flags.cache_clear()
