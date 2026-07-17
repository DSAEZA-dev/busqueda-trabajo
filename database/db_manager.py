import sqlite3
import json
from config.settings import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Para aplicar el cambio borramos la tabla anterior si existe (en un entorno real hariamos un ALTER)
    cursor.execute('DROP TABLE IF EXISTS historial_ofertas')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_ofertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rut TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            empresa TEXT,
            titulo TEXT,
            descripcion_breve TEXT,
            url TEXT,
            puntaje INTEGER,
            similitud REAL,
            pros TEXT,
            faltantes TEXT,
            consejo TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perfiles_usuario (
            rut TEXT PRIMARY KEY,
            region_casa TEXT,
            comuna_casa TEXT,
            cv_text TEXT,
            profesion_detectada TEXT,
            datos_perfil TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_user_profile(rut, region, comuna, cv_text, profesion, datos_perfil):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    datos_json = json.dumps(datos_perfil) if datos_perfil else "{}"
    cursor.execute('''
        INSERT OR REPLACE INTO perfiles_usuario (
            rut, region_casa, comuna_casa, cv_text, profesion_detectada, datos_perfil
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (rut, region, comuna, cv_text, profesion, datos_json))
    conn.commit()
    conn.close()

def get_user_profile(rut):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM perfiles_usuario WHERE rut=?', (rut,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "rut": row[0],
            "region_casa": row[1],
            "comuna_casa": row[2],
            "cv_text": row[3],
            "profesion_detectada": row[4],
            "datos_perfil": json.loads(row[5]) if row[5] else {}
        }
    return None

def save_oferta(rut, oferta):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO historial_ofertas (
            rut, empresa, titulo, descripcion_breve, url, puntaje, similitud, pros, faltantes, consejo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        rut,
        oferta.get("empresa", ""),
        oferta.get("titulo", ""),
        oferta.get("descripcion", "")[:200] + "...",
        oferta.get("url", ""),
        oferta.get("puntaje", 0),
        oferta.get("similitud_semantica", 0.0),
        json.dumps(oferta.get("pros", [])),
        json.dumps(oferta.get("faltantes", [])),
        oferta.get("consejo", "")
    ))
    conn.commit()
    conn.close()

def get_history(rut):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM historial_ofertas WHERE rut=? ORDER BY fecha DESC', (rut,))
    rows = cursor.fetchall()
    
    # Obtener los nombres de las columnas
    columns = [desc[0] for desc in cursor.description]
    
    # Convertir a lista de diccionarios
    historial = []
    for row in rows:
        historial.append(dict(zip(columns, row)))
        
    conn.close()
    return historial
