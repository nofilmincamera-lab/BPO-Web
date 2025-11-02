"""
Unified database connection manager.

This module provides a single source of truth for database connections,
eliminating 6x duplication across extraction scripts.

Centralized implementation ensures:
- Consistent connection configuration
- Proper password file handling (DB_PASSWORD_FILE or DB_PASSWORD env var)
- Connection pool reuse (singleton pattern)
- Both pool and direct connection methods
"""
import os
import asyncio
from typing import Optional
import asyncpg


# Global pool singleton
_DB_POOL: Optional[asyncpg.Pool] = None
_DB_POOL_LOCK = asyncio.Lock()


def _get_password() -> str:
    """
    Get database password from environment variable or password file.
    
    Priority:
    1. DB_PASSWORD environment variable (direct password)
    2. DB_PASSWORD_FILE environment variable (path to password file)
    3. Default to "postgres" for development (not recommended for production)
    
    Returns:
        Database password string
    """
    # Check direct password env var first
    password = os.getenv("DB_PASSWORD")
    if password:
        return password
    
    # Check password file env var
    password_file = os.getenv("DB_PASSWORD_FILE")
    if password_file and os.path.exists(password_file):
        try:
            with open(password_file, "r") as f:
                return f.read().strip()
        except Exception as e:
            raise RuntimeError(f"Failed to read password file {password_file}: {e}")
    
    # Default fallback (development only)
    return os.getenv("POSTGRES_PASSWORD", "postgres")


def get_db_config() -> dict:
    """
    Get standardized database configuration from environment variables.
    
    Returns:
        Dictionary with connection parameters:
        - host
        - port
        - database
        - user
        - password
        - min_size (pool minimum connections)
        - max_size (pool maximum connections)
    """
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
    """
    Get or create a shared asyncpg connection pool (singleton pattern).
    
    The pool is created once and reused across all calls. This improves
    performance by avoiding connection overhead on every database operation.
    
    Returns:
        Shared asyncpg.Pool instance
        
    Example:
        ```python
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM documents")
        ```
    """
    global _DB_POOL
    
    if _DB_POOL is None:
        async with _DB_POOL_LOCK:
            # Double-check after acquiring lock
            if _DB_POOL is None:
                config = get_db_config()
                _DB_POOL = await asyncpg.create_pool(**config)
    
    return _DB_POOL


async def get_db_connection() -> asyncpg.Connection:
    """
    Get a direct database connection (not from pool).
    
    Use this for long-running operations or when pool management is not needed.
    Caller must close the connection when done.
    
    Returns:
        asyncpg.Connection instance
        
    Example:
        ```python
        conn = await get_db_connection()
        try:
            rows = await conn.fetch("SELECT * FROM documents")
        finally:
            await conn.close()
        ```
    """
    config = get_db_config()
    # Remove pool-specific config
    config.pop("min_size", None)
    config.pop("max_size", None)
    return await asyncpg.connect(**config)


async def close_db_pool() -> None:
    """
    Close the shared database pool.
    
    Call this during application shutdown to properly clean up connections.
    After calling this, get_db_pool() will create a new pool on next access.
    """
    global _DB_POOL
    
    if _DB_POOL is not None:
        async with _DB_POOL_LOCK:
            if _DB_POOL is not None:
                await _DB_POOL.close()
                _DB_POOL = None


# Context manager for pool connections
class DBConnection:
    """
    Context manager for acquiring and releasing pool connections.
    
    Example:
        ```python
        pool = await get_db_pool()
        async with DBConnection(pool) as conn:
            rows = await conn.fetch("SELECT * FROM documents")
        ```
    """
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.conn: Optional[asyncpg.Connection] = None
    
    async def __aenter__(self) -> asyncpg.Connection:
        self.conn = await self.pool.acquire()
        return self.conn
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            await self.pool.release(self.conn)
            self.conn = None
