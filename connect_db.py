# BIS 698 - University Library Room Reservation System
# Central Michigan University
# Database connection and query execution utilities

import mysql.connector
from mysql.connector import Error
import credentials


def get_connection():
    """Return a new MySQL connection using credentials.py constants."""
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
    """
    Execute a single query.
    Returns list of dicts when fetch=True, else lastrowid.
    """
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
    """Execute a query for a list of parameter tuples (bulk insert/update)."""
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
