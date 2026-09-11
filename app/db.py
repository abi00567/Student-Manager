import os
import psycopg2

_db_initialized = False


def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Standardize postgres:// to postgresql:// for compatibility
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(db_url, connect_timeout=5)

    # Fallback to individual variables (for local development and Docker)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "studentdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres123"),
        connect_timeout=5
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            course VARCHAR(100) NOT NULL
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully.")


def ensure_db_initialized():
    global _db_initialized
    if not _db_initialized:
        try:
            init_db()
            _db_initialized = True
        except Exception as e:
            print("Database initialization notice:", e)
            raise e