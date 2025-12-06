from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    productos = db.relationship('Producto', backref='categoria', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    contacto = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    direccion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    productos = db.relationship('Producto', backref='proveedor', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'contacto': self.contacto,
            'telefono': self.telefono,
            'email': self.email,
            'direccion': self.direccion,
            'activo': self.activo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TipoMovimiento(db.Model):
    __tablename__ = 'tipos_movimiento'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    afecta_stock = db.Column(db.Boolean, default=True)
    signo = db.Column(db.Integer, nullable=False)  # -1 para salidas, 1 para entradas
    
    movimientos = db.relationship('Movimiento', backref='tipo_movimiento', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'afecta_stock': self.afecta_stock,
            'signo': self.signo
        }

class Rol(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    permisos = db.Column(db.JSON)  # Permisos en formato JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuarios = db.relationship('Usuario', backref='rol', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'permisos': self.permisos,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(200), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    ultimo_acceso = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    movimientos = db.relationship('Movimiento', backref='usuario', lazy=True)
    
    def set_password(self, password):
        """Hashea la contraseña de forma robusta"""
        try:
            if isinstance(password, str):
                password_bytes = password.encode('utf-8')
            else:
                password_bytes = password
            
            hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
            # Guardar como latin-1 para evitar problemas de encoding
            self.password_hash = hashed.decode('latin-1')
            
        except Exception as e:
            print(f"Error en set_password: {e}")
            raise

    def check_password(self, password):
        """Verifica la contraseña de forma robusta"""
        try:
            if not self.password_hash:
                return False
            
            # Convertir password a bytes
            if isinstance(password, str):
                password_bytes = password.encode('utf-8')
            else:
                password_bytes = password
            
            # Convertir hash almacenado a bytes
            if isinstance(self.password_hash, str):
                # Intentar con latin-1 primero (más robusto)
                stored_hash_bytes = self.password_hash.encode('latin-1')
            elif isinstance(self.password_hash, bytes):
                stored_hash_bytes = self.password_hash
            else:
                return False
            
            return bcrypt.checkpw(password_bytes, stored_hash_bytes)
            
        except Exception as e:
            print(f"Error en check_password: {e}")
            return False

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nombre_completo': self.nombre_completo,
            'rol': self.rol.to_dict() if self.rol else None,
            'activo': self.activo,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Producto(db.Model):
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    precio_compra = db.Column(db.Numeric(10, 2), default=0)
    precio_venta = db.Column(db.Numeric(10, 2), default=0)
    stock_actual = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    stock_maximo = db.Column(db.Integer)
    ubicacion = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    imagen_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    movimientos = db.relationship('Movimiento', backref='producto', lazy=True)
    alertas = db.relationship('Alerta', backref='producto', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'categoria': self.categoria.to_dict() if self.categoria else None,
            'proveedor': self.proveedor.to_dict() if self.proveedor else None,
            'precio_compra': float(self.precio_compra) if self.precio_compra else 0,
            'precio_venta': float(self.precio_venta) if self.precio_venta else 0,
            'stock_actual': self.stock_actual,
            'stock_minimo': self.stock_minimo,
            'stock_maximo': self.stock_maximo,
            'ubicacion': self.ubicacion,
            'activo': self.activo,
            'imagen_url': self.imagen_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'estado_stock': self.get_estado_stock()
        }
    
    def get_estado_stock(self):
        if self.stock_actual <= 0:
            return 'agotado'
        elif self.stock_actual < self.stock_minimo * 0.3:
            return 'critico'
        elif self.stock_actual < self.stock_minimo:
            return 'bajo'
        else:
            return 'normal'

class Movimiento(db.Model):
    __tablename__ = 'movimientos'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    tipo_movimiento_id = db.Column(db.Integer, db.ForeignKey('tipos_movimiento.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    cantidad_anterior = db.Column(db.Integer, nullable=False)
    cantidad_nueva = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.Text)
    referencia = db.Column(db.String(100))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'producto': self.producto.to_dict() if self.producto else None,
            'tipo_movimiento': self.tipo_movimiento.to_dict() if self.tipo_movimiento else None,
            'cantidad': self.cantidad,
            'cantidad_anterior': self.cantidad_anterior,
            'cantidad_nueva': self.cantidad_nueva,
            'motivo': self.motivo,
            'referencia': self.referencia,
            'usuario': self.usuario.to_dict() if self.usuario else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Alerta(db.Model):
    __tablename__ = 'alertas'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    tipo_alerta = db.Column(db.String(50), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    nivel = db.Column(db.String(20), nullable=False)
    leida = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'producto': self.producto.to_dict() if self.producto else None,
            'tipo_alerta': self.tipo_alerta,
            'mensaje': self.mensaje,
            'nivel': self.nivel,
            'leida': self.leida,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Configuracion(db.Model):
    __tablename__ = 'configuracion'
    
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text)
    descripcion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'clave': self.clave,
            'valor': self.valor,
            'descripcion': self.descripcion,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }