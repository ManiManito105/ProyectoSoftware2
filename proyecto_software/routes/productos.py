from flask import Blueprint, request, jsonify
from models import db, Producto, Categoria, Proveedor, Movimiento, TipoMovimiento
from auth import jwt_required, roles_required, get_jwt_identity
from sqlalchemy import or_

productos_bp = Blueprint('productos', __name__)

@productos_bp.route('/productos', methods=['GET'])
@jwt_required()
def obtener_productos():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        categoria_id = request.args.get('categoria_id', type=int)
        activo = request.args.get('activo', type=bool)
        
        query = Producto.query
        
        if search:
            query = query.filter(or_(
                Producto.nombre.ilike(f'%{search}%'),
                Producto.codigo.ilike(f'%{search}%'),
                Producto.descripcion.ilike(f'%{search}%')
            ))
        
        if categoria_id:
            query = query.filter(Producto.categoria_id == categoria_id)
        
        if activo is not None:
            query = query.filter(Producto.activo == activo)
        
        productos = query.order_by(Producto.nombre).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'productos': [producto.to_dict() for producto in productos.items],
            'total': productos.total,
            'paginas': productos.pages,
            'pagina_actual': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/productos/<int:id>', methods=['GET'])
@jwt_required()
def obtener_producto(id):
    try:
        producto = Producto.query.get_or_404(id)
        return jsonify(producto.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/productos', methods=['POST'])
@jwt_required()
@roles_required('admin', 'supervisor')
def crear_producto():
    try:
        data = request.get_json()
        
        # Verificar si el código ya existe
        if Producto.query.filter_by(codigo=data['codigo']).first():
            return jsonify({'error': 'El código del producto ya existe'}), 400
        
        producto = Producto(
            codigo=data['codigo'],
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            categoria_id=data.get('categoria_id'),
            proveedor_id=data.get('proveedor_id'),
            precio_compra=data.get('precio_compra', 0),
            precio_venta=data.get('precio_venta', 0),
            stock_actual=data.get('stock_actual', 0),
            stock_minimo=data.get('stock_minimo', 0),
            stock_maximo=data.get('stock_maximo'),
            ubicacion=data.get('ubicacion'),
            imagen_url=data.get('imagen_url')
        )
        
        db.session.add(producto)
        db.session.commit()
        
        return jsonify(producto.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/productos/<int:id>', methods=['PUT'])
@jwt_required()
@roles_required('admin', 'supervisor')
def actualizar_producto(id):
    try:
        producto = Producto.query.get_or_404(id)
        data = request.get_json()
        
        # Verificar si el código ya existe (excluyendo el producto actual)
        if 'codigo' in data and data['codigo'] != producto.codigo:
            if Producto.query.filter(Producto.codigo == data['codigo'], Producto.id != id).first():
                return jsonify({'error': 'El código del producto ya existe'}), 400
        
        # Actualizar campos
        for key, value in data.items():
            if hasattr(producto, key):
                setattr(producto, key, value)
        
        db.session.commit()
        
        return jsonify(producto.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/productos/<int:id>', methods=['DELETE'])
@jwt_required()
@roles_required('admin')
def eliminar_producto(id):
    try:
        producto = Producto.query.get_or_404(id)
        
        # Verificar si hay movimientos asociados
        if Movimiento.query.filter_by(producto_id=id).first():
            return jsonify({'error': 'No se puede eliminar el producto porque tiene movimientos asociados'}), 400
        
        db.session.delete(producto)
        db.session.commit()
        
        return jsonify({'mensaje': 'Producto eliminado correctamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/productos/stock-bajo', methods=['GET'])
@jwt_required()
def obtener_stock_bajo():
    try:
        productos = Producto.query.filter(
            Producto.stock_actual < Producto.stock_minimo,
            Producto.activo == True
        ).all()
        
        return jsonify([producto.to_dict() for producto in productos]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/categorias', methods=['GET'])
@jwt_required()
def obtener_categorias():
    try:
        categorias = Categoria.query.order_by(Categoria.nombre).all()
        return jsonify([categoria.to_dict() for categoria in categorias]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/proveedores', methods=['GET'])
@jwt_required()
def obtener_proveedores():
    try:
        proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
        return jsonify([proveedor.to_dict() for proveedor in proveedores]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500