from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from models import db, Producto, Movimiento, Categoria
from auth import jwt_required
from sqlalchemy import func, desc
from datetime import datetime, timedelta

reportes_bp = Blueprint('reportes', __name__)

@reportes_bp.route('/reportes/stock-categorias', methods=['GET'])
@jwt_required()
def reporte_stock_categorias():
    try:
        resultado = db.session.query(
            Categoria.nombre,
            func.count(Producto.id).label('total_productos'),
            func.sum(Producto.stock_actual).label('stock_total'),
            func.sum(Producto.stock_actual * Producto.precio_venta).label('valor_total')
        ).join(Producto, Producto.categoria_id == Categoria.id)\
         .filter(Producto.activo == True)\
         .group_by(Categoria.id, Categoria.nombre)\
         .all()
        
        reporte = []
        for cat in resultado:
            reporte.append({
                'categoria': cat.nombre,
                'total_productos': cat.total_productos,
                'stock_total': cat.stock_total or 0,
                'valor_total': float(cat.valor_total or 0)
            })
        
        return jsonify(reporte), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reportes_bp.route('/reportes/productos-mas-vendidos', methods=['GET'])
@jwt_required()
def reporte_productos_mas_vendidos():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        query = db.session.query(
            Producto.codigo,
            Producto.nombre,
            Categoria.nombre.label('categoria'),
            func.sum(Movimiento.cantidad).label('total_vendido'),
            func.sum(Movimiento.cantidad * Producto.precio_venta).label('ingresos_totales')
        ).join(Movimiento, Movimiento.producto_id == Producto.id)\
         .join(Categoria, Producto.categoria_id == Categoria.id)\
         .filter(Movimiento.tipo_movimiento_id.in_([2, 6]))  # Ventas y devoluciones a proveedor
        
        if fecha_inicio:
            fecha_inicio = datetime.fromisoformat(fecha_inicio)
            query = query.filter(Movimiento.created_at >= fecha_inicio)
        
        if fecha_fin:
            fecha_fin = datetime.fromisoformat(fecha_fin) + timedelta(days=1)
            query = query.filter(Movimiento.created_at < fecha_fin)
        
        resultado = query.group_by(Producto.id, Producto.codigo, Producto.nombre, Categoria.nombre)\
                        .order_by(desc('total_vendido'))\
                        .limit(10)\
                        .all()
        
        reporte = []
        for prod in resultado:
            reporte.append({
                'codigo': prod.codigo,
                'nombre': prod.nombre,
                'categoria': prod.categoria,
                'total_vendido': prod.total_vendido or 0,
                'ingresos_totales': float(prod.ingresos_totales or 0)
            })
        
        return jsonify(reporte), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reportes_bp.route('/reportes/movimientos-diarios', methods=['GET'])
@jwt_required()
def reporte_movimientos_diarios():
    try:
        fecha = request.args.get('fecha', datetime.utcnow().date().isoformat())
        fecha_obj = datetime.fromisoformat(fecha)
        
        movimientos = Movimiento.query.filter(
            func.date(Movimiento.created_at) == fecha_obj.date()
        ).order_by(Movimiento.created_at.desc()).all()
        
        return jsonify([movimiento.to_dict() for movimiento in movimientos]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reportes_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    try:
        # Eliminadas impresiones de depuración de cabeceras y JWT identity.
        # Total de productos
        total_productos = Producto.query.filter_by(activo=True).count()
        
        # Valor total del inventario
        valor_inventario = db.session.query(
            func.sum(Producto.stock_actual * Producto.precio_venta)
        ).filter(Producto.activo == True).scalar() or 0
        
        # Productos con stock bajo
        productos_stock_bajo = Producto.query.filter(
            Producto.stock_actual < Producto.stock_minimo,
            Producto.activo == True
        ).count()
        
        # Movimientos hoy
        hoy = datetime.utcnow().date()
        movimientos_hoy = Movimiento.query.filter(
            func.date(Movimiento.created_at) == hoy
        ).count()
        
        # Movimientos recientes
        movimientos_recientes = Movimiento.query.order_by(
            Movimiento.created_at.desc()
        ).limit(5).all()
        
        # Productos con stock crítico
        productos_criticos = Producto.query.filter(
            Producto.stock_actual < Producto.stock_minimo * 0.3,
            Producto.activo == True
        ).limit(5).all()
        
        return jsonify({
            'resumen': {
                'total_productos': total_productos,
                'valor_inventario': float(valor_inventario),
                'productos_stock_bajo': productos_stock_bajo,
                'movimientos_hoy': movimientos_hoy
            },
            'movimientos_recientes': [mov.to_dict() for mov in movimientos_recientes],
            'productos_criticos': [prod.to_dict() for prod in productos_criticos]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500