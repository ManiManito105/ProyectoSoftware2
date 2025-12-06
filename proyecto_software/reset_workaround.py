# reset_workaround.py
import psycopg2
import bcrypt

def reset_workaround():
    try:
        # Intenta conectar sin la contraseña problemática
        # Primero prueba sin contraseña
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='sistema_inventario',
                user='postgres'
                # Sin password
            )
        except:
            # Si falla, prueba con contraseña simple
            conn = psycopg2.connect(
                host='localhost',
                port=5432, 
                database='sistema_inventario',
                user='postgres',
                password='postgres'  # Contraseña común por defecto
            )
        
        cursor = conn.cursor()
        
        # Resto del código de reset...
        cursor.execute("SELECT id, username FROM usuarios;")
        usuarios = cursor.fetchall()
        
        for user_id, username in usuarios:
            print(f"Reseteando: {username}")
            nueva_password = "password123"
            password_bytes = nueva_password.encode('utf-8')
            hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
            new_hash_str = hashed.decode('latin-1')
            
            cursor.execute(
                "UPDATE usuarios SET password_hash = %s WHERE id = %s",
                (new_hash_str, user_id)
            )
        
        conn.commit()
        print("✅ ¡Éxito!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reset_workaround()