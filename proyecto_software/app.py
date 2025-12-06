from flask import Flask, jsonify
from flask import request
from flask_cors import CORS
from config import Config
from models import db
from auth import jwt, init_auth  # Cambiar esta línea
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar extensiones
    db.init_app(app)
    init_auth(app)  # Esta función ahora existe
    CORS(app)
    
    # Registrar blueprints
    from routes.auth_routes import auth_bp
    from routes.productos import productos_bp
    from routes.movimientos import movimientos_bp
    from routes.usuarios import usuarios_bp
    from routes.reportes import reportes_bp
    from routes.frontend import frontend_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(productos_bp, url_prefix='/api')
    app.register_blueprint(movimientos_bp, url_prefix='/api')
    app.register_blueprint(usuarios_bp, url_prefix='/api')
    app.register_blueprint(reportes_bp, url_prefix='/api')
    # Frontend (páginas HTML)
    app.register_blueprint(frontend_bp)

    # (Depuración eliminada) Antes teníamos logs temporales para Authorization.
    
    # Ruta de salud
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'OK', 'message': 'Sistema de Inventario API funcionando'})
    
    # Manejo de errores
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint no encontrado'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Error interno del servidor'}), 500

    # (Depuración eliminada) Endpoint temporal '/api/debug-headers' retirado.

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)