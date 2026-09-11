import os
import time
import psycopg2


def get_db_connection():
    return psycopg2.connect(
        os.getenv("DATABASE_URL")
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
            print(e)
            time.sleep(3)

    raise Exception("Could not connect to PostgreSQL.")