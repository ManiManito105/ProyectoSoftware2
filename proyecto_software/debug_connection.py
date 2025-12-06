# debug_connection.py
import psycopg2
import sys

def debug_connection():
    print("🔍 Debug de conexión...")
    
    # Probar diferentes combinaciones
    tests = [
        {"host": "localhost", "user": "postgres", "password": "password", "database": "sistema_inventario"},
        {"host": "127.0.0.1", "user": "postgres", "password": "password", "database": "sistema_inventario"},
    ]
    
    for i, test in enumerate(tests):
        print(f"\n🧪 Test {i+1}: {test}")
        try:
            conn = psycopg2.connect(**test)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            print(f"✅ Conexión exitosa: {cursor.fetchone()[0]}")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_connection()