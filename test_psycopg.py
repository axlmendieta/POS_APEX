import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

conn_info = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
print(f"Connecting with: host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER}")

try:
    with psycopg.connect(conn_info) as conn:
        print("Connected successfully!")
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            print(cur.fetchone())
except Exception as e:
    print(f"Error: {e}")
