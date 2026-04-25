# Central database access layer.
# Every query in the app goes through execute_query or execute_many.
# A fresh connection is opened and closed for each call — no persistent pool —
# which keeps things simple given the low concurrency of a desktop app.

import mysql.connector
from mysql.connector import Error
import credentials


def get_connection():
    # Opens a new connection using credentials imported from credentials.py.
    # Raises on failure so callers surface DB connectivity problems immediately.
    try:
        conn = mysql.connector.connect(
            host=credentials.DB_HOST,
            port=credentials.DB_PORT,
            database=credentials.DB_NAME,
            user=credentials.DB_USER,
            password=credentials.DB_PASSWORD,
            autocommit=False,
            connection_timeout=10,
        )
        return conn
    except Error as e:
        print(f"[DB] Connection error: {e}")
        raise


def execute_query(query, params=None, fetch=False):
    # Single-query helper used by every screen in the app.
    # fetch=True returns a list of dicts (dictionary cursor).
    # fetch=False commits the write and returns lastrowid.
    # Always closes cursor and connection in finally, even on error.
    conn   = None
    cursor = None
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        if fetch:
            return cursor.fetchall()
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        if conn:
            conn.rollback()
        print(f"[DB] Query error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def execute_many(query, data_list):
    # Bulk insert or update for a list of parameter tuples.
    # Uses executemany for efficiency; rolls back the entire batch on any error.
    conn   = None
    cursor = None
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, data_list)
        conn.commit()
    except Error as e:
        if conn:
            conn.rollback()
        print(f"[DB] Bulk query error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
