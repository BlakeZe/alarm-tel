import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "/app/data/alarmas.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Crea las tablas si no existen."""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alarmas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            moneda TEXT NOT NULL,
            condicion TEXT NOT NULL,
            precio REAL NOT NULL,
            activa INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            moneda TEXT NOT NULL,
            UNIQUE(chat_id, moneda)
        )
    """)

    conn.commit()
    conn.close()


# ── Alarmas 

def crear_alarma(chat_id, moneda, condicion, precio):
    conn = get_conn()
    conn.execute(
        "INSERT INTO alarmas (chat_id, moneda, condicion, precio) VALUES (?, ?, ?, ?)",
        (chat_id, moneda.upper(), condicion, precio)
    )
    conn.commit()
    conn.close()


def obtener_alarmas_activas():
    conn = get_conn()
    cursor = conn.execute("SELECT * FROM alarmas WHERE activa = 1")
    alarmas = cursor.fetchall()
    conn.close()
    return alarmas


def desactivar_alarma(alarma_id):
    conn = get_conn()
    conn.execute("UPDATE alarmas SET activa = 0 WHERE id = ?", (alarma_id,))
    conn.commit()
    conn.close()


def listar_alarmas(chat_id):
    conn = get_conn()
    cursor = conn.execute(
        "SELECT * FROM alarmas WHERE chat_id = ? AND activa = 1", (chat_id,)
    )
    alarmas = cursor.fetchall()
    conn.close()
    return alarmas


# ── Watchlist 

def watchlist_add(chat_id: str, moneda: str) -> bool:
    """Añade una moneda a la watchlist. Devuelve False si ya existía."""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO watchlist (chat_id, moneda) VALUES (?, ?)",
            (chat_id, moneda.upper())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def watchlist_remove(chat_id: str, moneda: str) -> bool:
    """Elimina una moneda de la watchlist. Devuelve False si no existía."""
    conn = get_conn()
    cursor = conn.execute(
        "DELETE FROM watchlist WHERE chat_id = ? AND moneda = ?",
        (chat_id, moneda.upper())
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def watchlist_get(chat_id: str) -> list[str]:
    """Devuelve la lista de monedas de un usuario."""
    conn = get_conn()
    cursor = conn.execute(
        "SELECT moneda FROM watchlist WHERE chat_id = ? ORDER BY moneda",
        (chat_id,)
    )
    monedas = [row[0] for row in cursor.fetchall()]
    conn.close()
    return monedas