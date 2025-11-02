"""
Unified database connection manager.

This module provides a single source of truth for database connections,
eliminating 6x duplication across extraction scripts.
"""
import os
import asyncio
from typing import Optional
import asyncpg


_DB_POOL: Optional[asyncpg.Pool] = None
_DB_POOL_LOCK = asyncio.Lock()


def _get_password() -> str:
    """Get database password from environment variable or password file."""
    password = os.getenv("DB_PASSWORD")
    if password:
        return password
    
    password_file = os.getenv("DB_PASSWORD_FILE")
    if password_file and os.path.exists(password_file):
        try:
            with open(password_file, "r") as f:
                return f.read().strip()
        except Exception as e:
            raise RuntimeError(f"Failed to read password file {password_file}: {e}")
    
    return os.getenv("POSTGRES_PASSWORD", "postgres")


def get_db_config() -> dict:
    """Get standardized database configuration from environment variables."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME", "bpo_intel"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": _get_password(),
        "min_size": int(os.getenv("DB_POOL_MIN_SIZE", 1)),
        "max_size": int(os.getenv("DB_POOL_MAX_SIZE", 10)),
    }


async def get_db_pool() -> asyncpg.Pool:
    """Get or create a shared asyncpg connection pool (singleton pattern)."""
    global _DB_POOL
    
    if _DB_POOL is None:
        async with _DB_POOL_LOCK:
            if _DB_POOL is None:
                config = get_db_config()
                _DB_POOL = await asyncpg.create_pool(**config)
    
    return _DB_POOL


async def get_db_connection() -> asyncpg.Connection:
    """Get a direct database connection (not from pool)."""
    config = get_db_config()
    config.pop("min_size", None)
    config.pop("max_size", None)
    return await asyncpg.connect(**config)
