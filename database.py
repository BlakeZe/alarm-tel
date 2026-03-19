import sqlite3
import os

# La base de datos se guarda en la carpeta /app/data dentro del contenedor
# que está mapeada a ~/alarm-tel/data en tu Raspberry Pi (el volume del docker-compose)
DB_PATH = "/app/data/alarmas.db"

def init_db():
    """Crea la tabla"""
    # Nos conectamos a la base de datos (la crea si no existe)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Creamos la tabla con las columnas que necesitamos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alarmas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,        -- a qué usuario avisar
            moneda TEXT NOT NULL,         -- ej: BTC, ETH
            condicion TEXT NOT NULL,      -- 'mayor' o 'menor'
            precio REAL NOT NULL,         -- precio objetivo
            activa INTEGER DEFAULT 1      -- 1=activa, 0=disparada
        )
    """)
    
    conn.commit()
    conn.close()

def crear_alarma(chat_id, moneda, condicion, precio):
    """Guarda una nueva alarma en bd"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alarmas (chat_id, moneda, condicion, precio) VALUES (?, ?, ?, ?)",
        (chat_id, moneda.upper(), condicion, precio)
    )
    conn.commit()
    conn.close()

def obtener_alarmas_activas():
    """Alarmas activas todos los usuarios"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alarmas WHERE activa = 1")
    alarmas = cursor.fetchall()
    conn.close()
    return alarmas

def desactivar_alarma(alarma_id):
    """Quita el estado de activa a una alarma"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE alarmas SET activa = 0 WHERE id = ?", (alarma_id,))
    conn.commit()
    conn.close()

def listar_alarmas(chat_id):
    """Devuelve las alarmas activas de un usuario concreto"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM alarmas WHERE chat_id = ? AND activa = 1",
        (chat_id,)
    )
    alarmas = cursor.fetchall()
    conn.close()
    return alarmas