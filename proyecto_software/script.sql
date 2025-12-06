-- Crear la base de datos
CREATE DATABASE sistema_inventario;

-- Extensión para UUID (opcional, pero útil)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla de categorías de productos
CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de proveedores
CREATE TABLE proveedores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    contacto VARCHAR(200),
    telefono VARCHAR(20),
    email VARCHAR(100),
    direccion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de tipos de movimiento
CREATE TABLE tipos_movimiento (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    afecta_stock BOOLEAN DEFAULT TRUE,
    signo INTEGER NOT NULL CHECK (signo IN (-1, 1)) -- -1 para salidas, 1 para entradas
);

-- Tabla de roles de usuario
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    permisos JSONB, -- Permisos en formato JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de usuarios
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(200) NOT NULL,
    rol_id INTEGER REFERENCES roles(id) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    ultimo_acceso TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de productos (DEBE ir después de las tablas que referencia)
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    categoria_id INTEGER REFERENCES categorias(id),
    proveedor_id INTEGER REFERENCES proveedores(id),
    precio_compra DECIMAL(10,2) NOT NULL DEFAULT 0,
    precio_venta DECIMAL(10,2) NOT NULL DEFAULT 0,
    stock_actual INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER NOT NULL DEFAULT 0,
    stock_maximo INTEGER,
    ubicacion VARCHAR(100),
    activo BOOLEAN DEFAULT TRUE,
    imagen_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de movimientos de inventario (DEBE ir después de productos y usuarios)
CREATE TABLE movimientos (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER REFERENCES productos(id) NOT NULL,
    tipo_movimiento_id INTEGER REFERENCES tipos_movimiento(id) NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    cantidad_anterior INTEGER NOT NULL,
    cantidad_nueva INTEGER NOT NULL,
    motivo TEXT,
    referencia VARCHAR(100), -- Número de factura, orden, etc.
    usuario_id INTEGER REFERENCES usuarios(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de alertas de inventario
CREATE TABLE alertas (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER REFERENCES productos(id) NOT NULL,
    tipo_alerta VARCHAR(50) NOT NULL, -- 'stock_bajo', 'stock_critico', 'sin_movimiento'
    mensaje TEXT NOT NULL,
    nivel VARCHAR(20) NOT NULL CHECK (nivel IN ('bajo', 'medio', 'alto', 'critico')),
    leida BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de configuración del sistema
CREATE TABLE configuracion (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de integración con sistemas externos
CREATE TABLE integraciones (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL, -- 'POS', 'SISTEMA_COMPRAS'
    url_base VARCHAR(500),
    api_key VARCHAR(500),
    activa BOOLEAN DEFAULT FALSE,
    configuracion JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de historial de sesiones
CREATE TABLE sesiones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) NOT NULL,
    token_sesion VARCHAR(500) NOT NULL,
    expira_en TIMESTAMP NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Restricciones CHECK sin subconsultas
ALTER TABLE productos 
ADD CONSTRAINT chk_precios_positivos 
CHECK (precio_compra >= 0 AND precio_venta >= 0);

ALTER TABLE productos 
ADD CONSTRAINT chk_stock_positivo 
CHECK (stock_actual >= 0 AND stock_minimo >= 0);

ALTER TABLE movimientos 
ADD CONSTRAINT chk_cantidad_positiva 
CHECK (cantidad > 0);

ALTER TABLE movimientos 
ADD CONSTRAINT chk_cantidades_no_negativas 
CHECK (cantidad_anterior >= 0 AND cantidad_nueva >= 0);

-- Restricciones adicionales para compatibilidad con la API
CREATE OR REPLACE FUNCTION validar_consistencia_movimiento()
RETURNS TRIGGER AS $$
DECLARE
    v_signo INTEGER;
    v_cantidad_calculada INTEGER;
BEGIN
    -- Obtener el signo del tipo de movimiento
    SELECT signo INTO v_signo 
    FROM tipos_movimiento 
    WHERE id = NEW.tipo_movimiento_id;
    
    -- Calcular la cantidad que debería ser
    v_cantidad_calculada := NEW.cantidad_anterior + (NEW.cantidad * v_signo);
    
    -- Verificar que coincida con cantidad_nueva
    IF NEW.cantidad_nueva != v_cantidad_calculada THEN
        RAISE EXCEPTION 'Inconsistencia en cantidades: anterior=%, cantidad=%, signo=%, calculada=%, nueva=%', 
            NEW.cantidad_anterior, NEW.cantidad, v_signo, v_cantidad_calculada, NEW.cantidad_nueva;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validar_movimiento
    BEFORE INSERT OR UPDATE ON movimientos
    FOR EACH ROW
    EXECUTE FUNCTION validar_consistencia_movimiento();



-- Índices para mejorar el rendimiento
CREATE INDEX idx_productos_categoria ON productos(categoria_id);
CREATE INDEX idx_productos_proveedor ON productos(proveedor_id);
CREATE INDEX idx_productos_activo ON productos(activo) WHERE activo = TRUE;
CREATE INDEX idx_productos_codigo ON productos(codigo);
CREATE INDEX idx_productos_stock ON productos(stock_actual) WHERE stock_actual < stock_minimo;

CREATE INDEX idx_movimientos_producto ON movimientos(producto_id);
CREATE INDEX idx_movimientos_fecha ON movimientos(created_at);
CREATE INDEX idx_movimientos_tipo ON movimientos(tipo_movimiento_id);
CREATE INDEX idx_movimientos_usuario ON movimientos(usuario_id);
CREATE INDEX idx_movimientos_referencia ON movimientos(referencia);

CREATE INDEX idx_usuarios_rol ON usuarios(rol_id);
CREATE INDEX idx_usuarios_activo ON usuarios(activo) WHERE activo = TRUE;
CREATE INDEX idx_usuarios_email ON usuarios(email);

CREATE INDEX idx_alertas_producto ON alertas(producto_id);
CREATE INDEX idx_alertas_leida ON alertas(leida) WHERE leida = FALSE;
CREATE INDEX idx_alertas_creado ON alertas(created_at DESC);

-- Insertar datos iniciales

-- Insertar categorías
INSERT INTO categorias (nombre, descripcion) VALUES
('Electrónicos', 'Dispositivos electrónicos y tecnología'),
('Ropa', 'Prendas de vestir y accesorios'),
('Hogar', 'Artículos para el hogar'),
('Deportes', 'Equipos y artículos deportivos'),
('Juguetes', 'Juguetes y juegos'),
('Oficina', 'Artículos de oficina y papelería');

-- Insertar tipos de movimiento
INSERT INTO tipos_movimiento (nombre, descripcion, afecta_stock, signo) VALUES
('compra', 'Entrada por compra a proveedor', TRUE, 1),
('venta', 'Salida por venta a cliente', TRUE, -1),
('ajuste_entrada', 'Ajuste manual de entrada', TRUE, 1),
('ajuste_salida', 'Ajuste manual de salida', TRUE, -1),
('devolucion_entrada', 'Devolución de cliente', TRUE, 1),
('devolucion_salida', 'Devolución a proveedor', TRUE, -1),
('transferencia_entrada', 'Entrada por transferencia', TRUE, 1),
('transferencia_salida', 'Salida por transferencia', TRUE, -1);

-- Insertar roles
INSERT INTO roles (nombre, descripcion, permisos) VALUES
('admin', 'Administrador del sistema', '{"productos": ["crear", "leer", "actualizar", "eliminar"], "movimientos": ["crear", "leer", "actualizar", "eliminar"], "reportes": ["leer"], "usuarios": ["crear", "leer", "actualizar", "eliminar"], "configuracion": ["leer", "actualizar"]}'),
('supervisor', 'Supervisor de inventario', '{"productos": ["crear", "leer", "actualizar"], "movimientos": ["crear", "leer", "actualizar"], "reportes": ["leer"], "usuarios": ["leer"], "configuracion": ["leer"]}'),
('operador', 'Operador de inventario', '{"productos": ["leer"], "movimientos": ["crear", "leer"], "reportes": ["leer"], "usuarios": ["leer"], "configuracion": ["leer"]}');

-- Insertar proveedores
INSERT INTO proveedores (nombre, contacto, telefono, email, direccion) VALUES
('Tecnología S.A.', 'Juan Pérez', '+1-234-567-8900', 'ventas@tecnologia.com', 'Av. Tecnología 123, Ciudad'),
('Moda Express', 'María García', '+1-234-567-8901', 'contacto@modaexpress.com', 'Calle Moda 456, Ciudad'),
('Deportes Total', 'Carlos López', '+1-234-567-8902', 'info@deportestotal.com', 'Blvd. Deportes 789, Ciudad'),
('Hogar y Cocina', 'Ana Martínez', '+1-234-567-8903', 'ventas@hogarycocina.com', 'Plaza Hogar 321, Ciudad');

-- Insertar usuarios (las contraseñas están hasheadas con bcrypt - todas son "password123")
INSERT INTO usuarios (username, email, password_hash, nombre_completo, rol_id) VALUES
('admin', 'admin@empresa.com', '$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Administrador Principal', 1),
('supervisor', 'supervisor@empresa.com', '$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Supervisor Inventario', 2),
('operador', 'operador@empresa.com', '$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Operador Ventas', 3);

-- Insertar productos
INSERT INTO productos (codigo, nombre, descripcion, categoria_id, proveedor_id, precio_compra, precio_venta, stock_actual, stock_minimo, stock_maximo, ubicacion) VALUES
('PROD-001', 'Laptop HP Pavilion', 'Laptop HP Pavilion 15.6" Intel Core i5 8GB RAM 256GB SSD', 1, 1, 8500.00, 12500.00, 15, 10, 50, 'Almacen A - Estante 1'),
('PROD-002', 'Mouse Inalámbrico', 'Mouse inalámbrico ergonómico 2.4GHz', 1, 1, 180.00, 350.00, 45, 20, 100, 'Almacen A - Estante 2'),
('PROD-003', 'Camisa Casual', 'Camisa casual de algodón talla M', 2, 2, 250.00, 450.00, 8, 15, 80, 'Almacen B - Estante 1'),
('PROD-004', 'Zapatos Deportivos', 'Zapatos deportivos para running talla 42', 4, 3, 700.00, 1200.00, 12, 10, 60, 'Almacen C - Estante 1'),
('PROD-005', 'Juego de Mesa', 'Juego de mesa familiar para 4-6 jugadores', 5, 4, 350.00, 650.00, 5, 8, 30, 'Almacen D - Estante 1'),
('PROD-006', 'Sartén Antiadherente', 'Sartén antiadherente 28cm de diámetro', 3, 4, 200.00, 380.00, 22, 15, 40, 'Almacen E - Estante 1');

-- Insertar movimientos de ejemplo
INSERT INTO movimientos (producto_id, tipo_movimiento_id, cantidad, cantidad_anterior, cantidad_nueva, motivo, referencia, usuario_id) VALUES
(1, 1, 10, 0, 10, 'Compra inicial de inventario', 'FAC-001', 1),
(2, 1, 50, 0, 50, 'Compra inicial de inventario', 'FAC-001', 1),
(1, 2, 5, 10, 5, 'Venta a cliente corporativo', 'VENTA-001', 3),
(3, 1, 20, 0, 20, 'Compra de temporada', 'FAC-002', 1),
(3, 4, 2, 20, 18, 'Ajuste por daño en almacén', 'AJUSTE-001', 2),
(4, 2, 8, 20, 12, 'Venta a tienda deportiva', 'VENTA-002', 3);

-- Insertar configuración del sistema
INSERT INTO configuracion (clave, valor, descripcion) VALUES
('empresa_nombre', 'Mi Empresa S.A.', 'Nombre de la empresa'),
('empresa_moneda', 'MXN', 'Moneda principal del sistema'),
('alertas_stock_bajo', 'true', 'Activar alertas por stock bajo'),
('alertas_stock_critico', 'true', 'Activar alertas por stock crítico'),
('stock_bajo_porcentaje', '20', 'Porcentaje para considerar stock bajo'),
('email_notificaciones', 'admin@empresa.com', 'Email para notificaciones');

-- Insertar integraciones
INSERT INTO integraciones (nombre, url_base, api_key, activa, configuracion) VALUES
('POS', 'https://pos.empresa.com/api', 'sk_test_123456789', true, '{"sincronizacion_automatica": true, "intervalo_sincronizacion": 300}'),
('SISTEMA_COMPRAS', 'https://compras.empresa.com/api', 'sk_compras_123456', true, '{"sincronizar_proveedores": true, "sincronizar_ordenes": true}');

-- Crear vistas útiles para reportes

-- Vista para productos con stock bajo
CREATE OR REPLACE VIEW vista_stock_bajo AS
SELECT 
    p.id,
    p.codigo,
    p.nombre,
    c.nombre as categoria,
    p.stock_actual,
    p.stock_minimo,
    (p.stock_minimo - p.stock_actual) as diferencia,
    CASE 
        WHEN p.stock_actual <= 0 THEN 'agotado'
        WHEN p.stock_actual < p.stock_minimo * 0.3 THEN 'critico'
        WHEN p.stock_actual < p.stock_minimo THEN 'bajo'
        ELSE 'normal'
    END as estado
FROM productos p
JOIN categorias c ON p.categoria_id = c.id
WHERE p.stock_actual < p.stock_minimo AND p.activo = true;

-- Vista para movimientos recientes
CREATE OR REPLACE VIEW vista_movimientos_recientes AS
SELECT 
    m.id,
    p.codigo,
    p.nombre as producto,
    tm.nombre as tipo_movimiento,
    tm.signo,
    m.cantidad,
    m.cantidad_anterior,
    m.cantidad_nueva,
    m.motivo,
    u.nombre_completo as usuario,
    m.created_at as fecha
FROM movimientos m
JOIN productos p ON m.producto_id = p.id
JOIN tipos_movimiento tm ON m.tipo_movimiento_id = tm.id
JOIN usuarios u ON m.usuario_id = u.id
ORDER BY m.created_at DESC;

-- Vista para reporte de productos más vendidos
CREATE OR REPLACE VIEW vista_productos_mas_vendidos AS
SELECT 
    p.id,
    p.codigo,
    p.nombre,
    c.nombre as categoria,
    SUM(CASE WHEN tm.signo = -1 THEN m.cantidad ELSE 0 END) as total_vendido,
    SUM(CASE WHEN tm.signo = -1 THEN m.cantidad * p.precio_venta ELSE 0 END) as ingresos_totales
FROM movimientos m
JOIN productos p ON m.producto_id = p.id
JOIN tipos_movimiento tm ON m.tipo_movimiento_id = tm.id
JOIN categorias c ON p.categoria_id = c.id
WHERE tm.signo = -1
GROUP BY p.id, p.codigo, p.nombre, c.nombre
ORDER BY total_vendido DESC;

-- Vista para valoración de inventario
CREATE OR REPLACE VIEW vista_valor_inventario AS
SELECT 
    c.nombre as categoria,
    COUNT(p.id) as cantidad_productos,
    SUM(p.stock_actual) as total_unidades,
    SUM(p.stock_actual * p.precio_compra) as valor_compra,
    SUM(p.stock_actual * p.precio_venta) as valor_venta
FROM productos p
JOIN categorias c ON p.categoria_id = c.id
WHERE p.activo = true
GROUP BY c.id, c.nombre;

-- Funciones y triggers

-- Función para actualizar el timestamp de updated_at
CREATE OR REPLACE FUNCTION actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para actualizar timestamps en todas las tablas
CREATE TRIGGER actualizar_categorias_timestamp 
    BEFORE UPDATE ON categorias 
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER actualizar_proveedores_timestamp 
    BEFORE UPDATE ON proveedores 
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER actualizar_productos_timestamp 
    BEFORE UPDATE ON productos 
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER actualizar_usuarios_timestamp 
    BEFORE UPDATE ON usuarios 
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER actualizar_movimientos_timestamp 
    BEFORE UPDATE ON movimientos 
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER actualizar_configuracion_timestamp 
    BEFORE UPDATE ON configuracion 
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER actualizar_integraciones_timestamp 
    BEFORE UPDATE ON integraciones 
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

-- Función para registrar movimiento y actualizar stock
CREATE OR REPLACE FUNCTION registrar_movimiento(
    p_producto_id INTEGER,
    p_tipo_movimiento_id INTEGER,
    p_cantidad INTEGER,
    p_usuario_id INTEGER,
    p_motivo TEXT DEFAULT NULL,
    p_referencia VARCHAR(100) DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_cantidad_anterior INTEGER;
    v_cantidad_nueva INTEGER;
    v_signo INTEGER;
    v_movimiento_id INTEGER;
    v_afecta_stock BOOLEAN;
BEGIN
    -- Verificar que el producto existe y está activo
    IF NOT EXISTS (SELECT 1 FROM productos WHERE id = p_producto_id AND activo = true) THEN
        RAISE EXCEPTION 'Producto no encontrado o inactivo';
    END IF;
    
    -- Obtener stock actual y signo del tipo de movimiento
    SELECT stock_actual INTO v_cantidad_anterior FROM productos WHERE id = p_producto_id;
    SELECT signo, afecta_stock INTO v_signo, v_afecta_stock FROM tipos_movimiento WHERE id = p_tipo_movimiento_id;
    
    IF v_signo IS NULL THEN
        RAISE EXCEPTION 'Tipo de movimiento no válido';
    END IF;
    
    -- Calcular nueva cantidad
    IF v_afecta_stock THEN
        v_cantidad_nueva := v_cantidad_anterior + (p_cantidad * v_signo);
        
        -- Verificar que el stock no sea negativo
        IF v_cantidad_nueva < 0 THEN
            RAISE EXCEPTION 'Stock insuficiente. Stock actual: %, intentando sacar: %', v_cantidad_anterior, p_cantidad;
        END IF;
    ELSE
        v_cantidad_nueva := v_cantidad_anterior;
    END IF;
    
    -- Insertar movimiento
    INSERT INTO movimientos (producto_id, tipo_movimiento_id, cantidad, cantidad_anterior, cantidad_nueva, motivo, referencia, usuario_id)
    VALUES (p_producto_id, p_tipo_movimiento_id, p_cantidad, v_cantidad_anterior, v_cantidad_nueva, p_motivo, p_referencia, p_usuario_id)
    RETURNING id INTO v_movimiento_id;
    
    -- Actualizar stock del producto si afecta stock
    IF v_afecta_stock THEN
        UPDATE productos 
        SET stock_actual = v_cantidad_nueva, updated_at = CURRENT_TIMESTAMP 
        WHERE id = p_producto_id;
    END IF;
    
    RETURN v_movimiento_id;
END;
$$ LANGUAGE plpgsql;

-- Función para generar alertas de stock bajo
CREATE OR REPLACE FUNCTION generar_alertas_stock()
RETURNS VOID AS $$
BEGIN
    -- Alertas para stock crítico (menos del 30% del mínimo)
    INSERT INTO alertas (producto_id, tipo_alerta, mensaje, nivel)
    SELECT 
        id,
        'stock_critico',
        'Stock crítico: ' || nombre || ' tiene ' || stock_actual || ' unidades (mínimo: ' || stock_minimo || ')',
        'critico'
    FROM productos 
    WHERE stock_actual < stock_minimo * 0.3 
    AND stock_actual > 0
    AND activo = true
    AND NOT EXISTS (
        SELECT 1 FROM alertas 
        WHERE producto_id = productos.id 
        AND tipo_alerta = 'stock_critico' 
        AND leida = false
        AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 day'
    );
    
    -- Alertas para stock agotado
    INSERT INTO alertas (producto_id, tipo_alerta, mensaje, nivel)
    SELECT 
        id,
        'stock_agotado',
        'Stock agotado: ' || nombre || ' tiene 0 unidades (mínimo: ' || stock_minimo || ')',
        'critico'
    FROM productos 
    WHERE stock_actual <= 0
    AND activo = true
    AND NOT EXISTS (
        SELECT 1 FROM alertas 
        WHERE producto_id = productos.id 
        AND tipo_alerta = 'stock_agotado' 
        AND leida = false
        AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 day'
    );
    
    -- Alertas para stock bajo (menos del mínimo)
    INSERT INTO alertas (producto_id, tipo_alerta, mensaje, nivel)
    SELECT 
        id,
        'stock_bajo',
        'Stock bajo: ' || nombre || ' tiene ' || stock_actual || ' unidades (mínimo: ' || stock_minimo || ')',
        'alto'
    FROM productos 
    WHERE stock_actual < stock_minimo 
    AND stock_actual >= stock_minimo * 0.3
    AND activo = true
    AND NOT EXISTS (
        SELECT 1 FROM alertas 
        WHERE producto_id = productos.id 
        AND tipo_alerta = 'stock_bajo' 
        AND leida = false
        AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 day'
    );
END;
$$ LANGUAGE plpgsql;

-- Trigger para generar alertas automáticamente después de movimientos
CREATE OR REPLACE FUNCTION generar_alertas_despues_movimiento()
RETURNS TRIGGER AS $$
BEGIN
    -- Ejecutar generación de alertas
    PERFORM generar_alertas_stock();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_alertas_movimiento
    AFTER INSERT ON movimientos
    FOR EACH ROW
    EXECUTE FUNCTION generar_alertas_despues_movimiento();

-- Comentarios en las tablas
COMMENT ON TABLE categorias IS 'Almacena las categorías de productos';
COMMENT ON TABLE proveedores IS 'Información de proveedores de productos';
COMMENT ON TABLE productos IS 'Almacena la información de los productos del inventario';
COMMENT ON TABLE tipos_movimiento IS 'Tipos de movimientos de inventario (entradas/salidas)';
COMMENT ON TABLE movimientos IS 'Registra todos los movimientos de entrada y salida de productos';
COMMENT ON TABLE usuarios IS 'Usuarios del sistema con sus roles y permisos';
COMMENT ON TABLE roles IS 'Roles de usuario y permisos del sistema';
COMMENT ON TABLE alertas IS 'Sistema de alertas para stock bajo y otros eventos';
COMMENT ON TABLE configuracion IS 'Configuración general del sistema';
COMMENT ON TABLE integraciones IS 'Configuración de integraciones con sistemas externos';
COMMENT ON TABLE sesiones IS 'Control de sesiones de usuario activas';

-- Función para inicializar la base de datos (opcional)
CREATE OR REPLACE FUNCTION inicializar_base_datos()
RETURNS VOID AS $$
BEGIN
    -- Ejecutar generación inicial de alertas
    PERFORM generar_alertas_stock();
    
    -- Mensaje de éxito
    RAISE NOTICE 'Base de datos sistema_inventario inicializada exitosamente!';
END;
$$ LANGUAGE plpgsql;

-- Permisos para el usuario de la aplicación (ajusta según tu configuración)
-- CREATE USER app_user WITH PASSWORD 'password_seguro';
-- GRANT CONNECT ON DATABASE sistema_inventario TO app_user;
-- GRANT USAGE ON SCHEMA public TO app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Ejecutar la inicialización
SELECT inicializar_base_datos();

-- reset_passwords.sql
UPDATE usuarios SET password_hash = '$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi' WHERE username = 'admin';
UPDATE usuarios SET password_hash = '$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi' WHERE username = 'supervisor';
UPDATE usuarios SET password_hash = '$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi' WHERE username = 'operador';