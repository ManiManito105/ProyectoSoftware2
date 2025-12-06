# test_connection.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_database_connection():
    try:
        # Obtener la URL de la base de datos
        database_url = os.environ.get('DATABASE_URL')
        print(f"Database URL: {database_url}")
        
        if not database_url:
            print("❌ DATABASE_URL no encontrada en .env")
            return False
        
        # Probar conexión directa con psycopg2
        print("🔍 Probando conexión directa...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Probar consulta simple
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL version: {version[0]}")
        
        # Probar consulta de usuarios
        cursor.execute("SELECT id, username FROM usuarios;")
        usuarios = cursor.fetchall()
        print(f"✅ Usuarios encontrados: {len(usuarios)}")
        for usuario in usuarios:
            print(f"   - ID: {usuario[0]}, Username: {usuario[1]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()