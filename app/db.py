import os
import time
import psycopg2


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "studentdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )


def init_db():
    for attempt in range(10):
        try:
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
            return

        except Exception as e:
            print(f"Database not ready. Attempt {attempt + 1}/10")
            time.sleep(3)

    raise Exception("Could not connect to PostgreSQL.")