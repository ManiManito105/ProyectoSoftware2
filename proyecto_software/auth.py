from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask import jsonify
from functools import wraps
from models import Usuario

jwt = JWTManager()

def init_auth(app):
    jwt.init_app(app)
    
    # CORREGIDO: La identity ya es el ID, no necesita procesamiento
    @jwt.user_identity_loader
    def user_identity_lookup(identity):
        """
        identity ya es el user_id (entero) que pasamos en create_access_token
        Solo lo devolvemos tal cual
        """
        # Asegurar que la 'sub' del JWT sea una cadena, porque PyJWT espera un 'subject' string
        try:
            return str(identity) if identity is not None else None
        except Exception:
            return identity
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """
        Esta función se usa para cargar el usuario cuando se usa current_user
        """
        identity = jwt_data["sub"]
        return Usuario.query.get(identity)

    # Callbacks para depuración de errores JWT
    @jwt.unauthorized_loader
    def jwt_unauthorized_callback(message):
        # Registro temporal eliminado
        return jsonify({'error': message}), 401

    @jwt.invalid_token_loader
    def jwt_invalid_token_callback(message):
        # Registro temporal eliminado
        return jsonify({'error': message}), 422

    @jwt.expired_token_loader
    def jwt_expired_token_callback(jwt_header, jwt_payload):
        # Registro temporal eliminado
        return jsonify({'error': 'Token expirado'}), 401

    @jwt.revoked_token_loader
    def jwt_revoked_token_callback(jwt_header, jwt_payload):
        # Registro temporal eliminado
        return jsonify({'error': 'Token revocado'}), 401

# O si quieres una versión más simple, elimina las funciones personalizadas:
def init_auth_simple(app):
    jwt.init_app(app)

def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = Usuario.query.get(current_user_id)
            
            if not user or user.rol.nombre not in roles:
                return {'error': 'No tienes permisos para realizar esta acción'}, 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper