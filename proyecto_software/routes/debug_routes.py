from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, Usuario
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        print(f"📨 Datos recibidos: {data}")
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Se requiere username y password'}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        print(f"🔍 Buscando usuario: {username}")
        
        usuario = Usuario.query.filter_by(username=username).first()
        
        if not usuario:
            print("❌ Usuario no encontrado")
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        print(f"✅ Usuario encontrado: {usuario.username}, ID: {usuario.id}")
        print(f"📊 Hash almacenado tipo: {type(usuario.password_hash)}")
        
        # Verificar contraseña
        try:
            password_valida = usuario.check_password(password)
            print(f"🔑 Resultado verificación: {password_valida}")
        except Exception as check_error:
            print(f"❌ Error en check_password: {check_error}")
            password_valida = False
        
        if not password_valida:
            print("❌ Contraseña inválida")
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        if not usuario.activo:
            return jsonify({'error': 'Usuario inactivo'}), 401
        
        # Actualizar último acceso
        usuario.ultimo_acceso = datetime.utcnow()
        db.session.commit()
        
        # CORREGIDO: Asegurarnos de que identity sea solo el ID
        user_id = usuario.id
        print(f"🎫 Creando token para user_id: {user_id} (tipo: {type(user_id)})")
        
        access_token = create_access_token(identity=user_id)
        
        # Preparar respuesta del usuario (sin el método to_dict problemático)
        usuario_data = {
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'nombre_completo': usuario.nombre_completo,
            'activo': usuario.activo,
            'rol_id': usuario.rol_id
        }
        
        print(f"✅ Login exitoso para: {usuario.username}")
        
        return jsonify({
            'access_token': access_token,
            'usuario': usuario_data
        }), 200
        
    except Exception as e:
        print(f"💥 ERROR GENERAL EN LOGIN: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error interno del servidor'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        current_user_id = get_jwt_identity()
        print(f"🔍 Buscando usuario con ID: {current_user_id}")
        
        usuario = Usuario.query.get(current_user_id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Usar el mismo formato que en login
        usuario_data = {
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'nombre_completo': usuario.nombre_completo,
            'activo': usuario.activo,
            'rol_id': usuario.rol_id
        }
        
        return jsonify(usuario_data), 200
        
    except Exception as e:
        print(f"Error en /me: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500
    
@auth_bp.route('/debug/password', methods=['POST'])
def debug_password():
    """Endpoint temporal para diagnosticar problemas de contraseña"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        usuario = Usuario.query.filter_by(username=username).first()
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        debug_info = {
            'username': usuario.username,
            'password_hash_type': str(type(usuario.password_hash)),
            'password_hash_length': len(usuario.password_hash) if usuario.password_hash else 0,
            'password_hash_sample': str(usuario.password_hash)[:100] if usuario.password_hash else None,
            'is_binary': isinstance(usuario.password_hash, bytes)
        }
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500