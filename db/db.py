import duckdb
import os
from app.config import get_config


def get_db_connection():
    db_path = get_config("DB_PATH", "./data/processed/amazon.db")
    conn = duckdb.connect(database=db_path, read_only=False)
    return conn
