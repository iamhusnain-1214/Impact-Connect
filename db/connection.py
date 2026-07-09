import mysql.connector
from mysql.connector import pooling, Error
from config import Config

# ---------------------------------------------------------------------------
# Connection strategy for a serverless target (Vercel).
#
# The previous version built a 10-connection pool at MODULE IMPORT TIME.
# That's fine on a normal long-running server (Railway/Render), but it's a
# real problem on Vercel:
#
#   - Every serverless invocation can run in its own function instance.
#     Under real traffic, dozens of instances can spin up in parallel, each
#     one trying to open its OWN 10-connection pool at cold start. A small
#     hosted MySQL plan (PlanetScale/Aiven free tier, Railway hobby, etc.)
#     typically caps out around 10-60 total connections - so this pattern
#     exhausts the DB's connection limit almost immediately under any real
#     concurrency, and every request starts failing with "Too many
#     connections".
#   - Building the pool at import time also slows down every cold start,
#     since Vercel has to finish that work before the function can respond
#     to its first request.
#
# Fix: the pool is created LAZILY (on first use, not at import), and sized
# small (pool_size=3) since each function instance only ever needs a
# handful of connections for itself, not ten. SSL is enabled by default
# because hosted MySQL providers (PlanetScale, TiDB Cloud, Aiven, Railway)
# require or strongly prefer TLS - local MySQL doesn't care either way, so
# this is safe for local dev too.
# ---------------------------------------------------------------------------

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        pool_kwargs = dict(
            pool_name="impactconnect_pool",
            pool_size=Config.DB_POOL_SIZE,
            pool_reset_session=True,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            connection_timeout=5,
        )
        if Config.DB_USE_SSL:
            pool_kwargs["ssl_disabled"] = False
            
        try:
            _pool = pooling.MySQLConnectionPool(**pool_kwargs)
        except Error as e:
            print(f"[DB ERROR] Could not create connection pool: {e}")
            raise
    return _pool


def get_connection():
    """
    Borrows a connection from the (lazily-created) pool. Call .close() as
    usual when done - that returns the connection to the pool rather than
    actually closing the socket.
    """
    try:
        return _get_pool().get_connection()
    except Error as e:
        print(f"[DB ERROR] Could not get pooled connection: {e}")
        raise


def test_connection():
    """Quick sanity check you can run directly: python -m db.connection"""
    conn = get_connection()
    if conn.is_connected():
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()
        print(f"✅ Connected successfully to database: {db_name[0]}")
        cursor.close()
    conn.close()


if __name__ == "__main__":
    test_connection()
