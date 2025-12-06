from flask import Blueprint, request, jsonify
from models import db, Movimiento, Producto, TipoMovimiento, Usuario
from auth import jwt_required, roles_required, get_jwt_identity
from datetime import datetime, timedelta

movimientos_bp = Blueprint('movimientos', __name__)

@movimientos_bp.route('/movimientos', methods=['GET'])
@jwt_required()
def obtener_movimientos():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        producto_id = request.args.get('producto_id', type=int)
        tipo_movimiento_id = request.args.get('tipo_movimiento_id', type=int)
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        query = Movimiento.query
        
        if producto_id:
            query = query.filter(Movimiento.producto_id == producto_id)
        
        if tipo_movimiento_id:
            query = query.filter(Movimiento.tipo_movimiento_id == tipo_movimiento_id)
        
        if fecha_inicio:
            fecha_inicio = datetime.fromisoformat(fecha_inicio)
            query = query.filter(Movimiento.created_at >= fecha_inicio)
        
        if fecha_fin:
            fecha_fin = datetime.fromisoformat(fecha_fin) + timedelta(days=1)
            query = query.filter(Movimiento.created_at < fecha_fin)
        
        movimientos = query.order_by(Movimiento.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'movimientos': [movimiento.to_dict() for movimiento in movimientos.items],
            'total': movimientos.total,
            'paginas': movimientos.pages,
            'pagina_actual': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@movimientos_bp.route('/movimientos', methods=['POST'])
@jwt_required()
@roles_required('admin', 'supervisor', 'operador')
def crear_movimiento():
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        producto = Producto.query.get_or_404(data['producto_id'])
        tipo_movimiento = TipoMovimiento.query.get_or_404(data['tipo_movimiento_id'])
        
        # Calcular nuevas cantidades
        cantidad_anterior = producto.stock_actual
        cantidad_nueva = cantidad_anterior + (data['cantidad'] * tipo_movimiento.signo)
        
        # Verificar que no quede stock negativo
        if cantidad_nueva < 0:
            return jsonify({'error': 'No hay suficiente stock para realizar este movimiento'}), 400
        
        movimiento = Movimiento(
            producto_id=data['producto_id'],
            tipo_movimiento_id=data['tipo_movimiento_id'],
            cantidad=data['cantidad'],
            cantidad_anterior=cantidad_anterior,
            cantidad_nueva=cantidad_nueva,
            motivo=data.get('motivo'),
            referencia=data.get('referencia'),
            usuario_id=current_user_id
        )
        
        # Actualizar stock del producto
        producto.stock_actual = cantidad_nueva
        
        db.session.add(movimiento)
        db.session.commit()
        
        return jsonify(movimiento.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@movimientos_bp.route('/movimientos/<int:id>', methods=['GET'])
@jwt_required()
def obtener_movimiento(id):
    try:
        movimiento = Movimiento.query.get_or_404(id)
        return jsonify(movimiento.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@movimientos_bp.route('/tipos-movimiento', methods=['GET'])
@jwt_required()
def obtener_tipos_movimiento():
    try:
        tipos = TipoMovimiento.query.order_by(TipoMovimiento.nombre).all()
        return jsonify([tipo.to_dict() for tipo in tipos]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    