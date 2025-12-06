from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, Usuario
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Se requiere username y password'}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        usuario = Usuario.query.filter_by(username=username).first()
        
        if not usuario or not usuario.check_password(password):
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        if not usuario.activo:
            return jsonify({'error': 'Usuario inactivo'}), 401
        
        # Actualizar último acceso
        usuario.ultimo_acceso = datetime.utcnow()
        db.session.commit()
        
        # Crear token
        access_token = create_access_token(identity=usuario.id)
        
        # Preparar respuesta del usuario
        usuario_data = {
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'nombre_completo': usuario.nombre_completo,
            'activo': usuario.activo,
            'rol_id': usuario.rol_id
        }
        
        print("✅ Login exitoso")
        
        return jsonify({
            'access_token': access_token,
            'usuario': usuario_data
        }), 200
        
    except Exception as e:
        print(f"Error en login: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        current_user_id = get_jwt_identity()
        
        usuario = Usuario.query.get(current_user_id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
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