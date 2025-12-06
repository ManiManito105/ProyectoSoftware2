# reset_passwords.py
import sys
import os
import bcrypt

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def reset_all_passwords():
    try:
        from app import create_app
        from models import db, Usuario
        
        # Crear la aplicación
        app = create_app()
        
        with app.app_context():
            # Obtener todos los usuarios
            usuarios = Usuario.query.all()
            
            print(f"Encontrados {len(usuarios)} usuarios:")
            
            for usuario in usuarios:
                print(f"Reseteando contraseña para: {usuario.username}")
                
                # Contraseña temporal
                nueva_password = "password123"
                
                # Crear hash directamente (evitando posibles problemas en set_password)
                password_bytes = nueva_password.encode('utf-8')
                hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
                
                # Guardar como string latin-1 (más robusto)
                usuario.password_hash = hashed.decode('latin-1')
                
                print(f"✅ Nueva contraseña para {usuario.username}: {nueva_password}")
            
            # Guardar cambios
            db.session.commit()
            print(f"\n✅ ¡Todas las contraseñas fueron reseteadas a 'password123'!")
            print("Ahora puedes iniciar sesión con:")
            for usuario in usuarios:
                print(f"   Usuario: {usuario.username} | Contraseña: password123")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_all_passwords()