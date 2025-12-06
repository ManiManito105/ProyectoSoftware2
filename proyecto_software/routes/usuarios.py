from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Usuario, Rol
from functools import wraps

usuarios_bp = Blueprint('usuarios', __name__)

# Decorator personalizado para roles (AGREGAR ESTO)
def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            current_user_id = get_jwt_identity()
            usuario = Usuario.query.get(current_user_id)
            
            if not usuario or usuario.rol.nombre not in roles:
                return jsonify({'error': 'No tienes permisos para realizar esta acción'}), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

@usuarios_bp.route('/usuarios', methods=['GET'])
@jwt_required()
@roles_required('admin')
def obtener_usuarios():
    try:
        usuarios = Usuario.query.all()
        return jsonify([usuario.to_dict() for usuario in usuarios]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@usuarios_bp.route('/usuarios/<int:id>', methods=['GET'])
@jwt_required()
def obtener_usuario(id):
    try:
        current_user_id = get_jwt_identity()
        current_user = Usuario.query.get(current_user_id)
        
        # Los usuarios solo pueden ver su propio perfil, a menos que sean admin
        if current_user.rol.nombre != 'admin' and current_user_id != id:
            return jsonify({'error': 'No tienes permisos para ver este usuario'}), 403
        
        usuario = Usuario.query.get_or_404(id)
        return jsonify(usuario.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@usuarios_bp.route('/usuarios', methods=['POST'])
@jwt_required()
@roles_required('admin')
def crear_usuario():
    try:
        data = request.get_json()
        
        # Validaciones requeridas
        required_fields = ['username', 'email', 'nombre_completo', 'rol_id', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'El campo {field} es requerido'}), 400
        
        # Verificar si el username o email ya existen
        if Usuario.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'El nombre de usuario ya existe'}), 400
        
        if Usuario.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'El email ya está registrado'}), 400
        
        # Verificar que el rol existe
        rol = Rol.query.get(data['rol_id'])
        if not rol:
            return jsonify({'error': 'El rol especificado no existe'}), 400
        
        usuario = Usuario(
            username=data['username'].strip(),
            email=data['email'].strip(),
            nombre_completo=data['nombre_completo'].strip(),
            rol_id=data['rol_id']
        )
        
        usuario.set_password(data['password'])
        
        db.session.add(usuario)
        db.session.commit()
        
        return jsonify(usuario.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        # Mensaje de error detallado para logs removido (debugging temporal)
        return jsonify({'error': 'Error interno del servidor'}), 500

@usuarios_bp.route('/usuarios/<int:id>', methods=['PUT'])
@jwt_required()
def actualizar_usuario(id):
    try:
        current_user_id = get_jwt_identity()
        current_user = Usuario.query.get(current_user_id)
        
        # Los usuarios solo pueden actualizar su propio perfil, a menos que sean admin
        if current_user.rol.nombre != 'admin' and current_user_id != id:
            return jsonify({'error': 'No tienes permisos para actualizar este usuario'}), 403
        
        usuario = Usuario.query.get_or_404(id)
        data = request.get_json()
        
        # Verificar si el username o email ya existen (excluyendo el usuario actual)
        if 'username' in data and data['username'] != usuario.username:
            username = data['username'].strip()
            if Usuario.query.filter(Usuario.username == username, Usuario.id != id).first():
                return jsonify({'error': 'El nombre de usuario ya existe'}), 400
            usuario.username = username
        
        if 'email' in data and data['email'] != usuario.email:
            email = data['email'].strip()
            if Usuario.query.filter(Usuario.email == email, Usuario.id != id).first():
                return jsonify({'error': 'El email ya está registrado'}), 400
            usuario.email = email
        
        # Actualizar campos permitidos
        allowed_fields = ['nombre_completo', 'rol_id', 'activo']
        for key, value in data.items():
            if key == 'password':
                usuario.set_password(value)
            elif key in allowed_fields and hasattr(usuario, key):
                if key == 'nombre_completo':
                    setattr(usuario, key, value.strip())
                else:
                    setattr(usuario, key, value)
        
        db.session.commit()
        
        return jsonify(usuario.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        # Mensaje de error detallado para logs removido (debugging temporal)
        return jsonify({'error': 'Error interno del servidor'}), 500

@usuarios_bp.route('/roles', methods=['GET'])
@jwt_required()
@roles_required('admin')
def obtener_roles():
    try:
        roles = Rol.query.all()
        return jsonify([rol.to_dict() for rol in roles]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    
def check_password(self, password):
    """Verifica la contraseña con manejo robusto de encoding"""
    try:
        # Asegurar que la contraseña ingresada está en bytes
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
        else:
            password_bytes = password
        
        # Manejar el hash almacenado
        stored_hash = self.password_hash
        
        # Si el hash almacenado es string, convertirlo a bytes
        if isinstance(stored_hash, str):
            try:
                # Intentar decodificar como UTF-8 primero
                stored_hash = stored_hash.encode('utf-8')
            except UnicodeEncodeError:
                # Si falla, usar latin-1 que maneja todos los bytes
                stored_hash = stored_hash.encode('latin-1')
        
        # Verificar la contraseña
        return bcrypt.checkpw(password_bytes, stored_hash)
        
    except Exception:
        # Evitar imprimir detalles de error en producción
        return False