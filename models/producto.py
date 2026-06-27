from database.db import db
from datetime import datetime

class Laboratorio(db.Model):
    __tablename__ = 'laboratorio'
    
    id_laboratorio = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    pais = db.Column(db.String(50))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    direccion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    marcas = db.relationship('Marca', backref='laboratorio', lazy=True)
    productos = db.relationship('Producto', backref='laboratorio_ref', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_laboratorio,
            'nombre': self.nombre,
            'pais': self.pais,
            'telefono': self.telefono,
            'email': self.email
        }

class Marca(db.Model):
    __tablename__ = 'marca'
    
    id_marca = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    id_laboratorio = db.Column(db.Integer, db.ForeignKey('laboratorio.id_laboratorio'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    productos = db.relationship('Producto', backref='marca_ref', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_marca,
            'nombre': self.nombre,
            'laboratorio': self.laboratorio.nombre if self.laboratorio else None
        }

class Categoria(db.Model):
    __tablename__ = 'categoria'
    
    id_categoria = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    productos = db.relationship('Producto', backref='categoria_ref', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_categoria,
            'nombre': self.nombre,
            'descripcion': self.descripcion
        }

class Producto(db.Model):
    __tablename__ = 'producto'
    
    id_producto = db.Column(db.Integer, primary_key=True)
    codigo_barras = db.Column(db.String(50), unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    id_marca = db.Column(db.Integer, db.ForeignKey('marca.id_marca'))
    id_categoria = db.Column(db.Integer, db.ForeignKey('categoria.id_categoria'))
    id_laboratorio = db.Column(db.Integer, db.ForeignKey('laboratorio.id_laboratorio'))
    presentacion = db.Column(db.String(50))
    concentracion = db.Column(db.String(50))
    precio_compra = db.Column(db.Numeric(10, 2), nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    stock_actual = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    stock_maximo = db.Column(db.Integer, default=100)
    fecha_vencimiento = db.Column(db.Date)
    imagen_url = db.Column(db.String(255))
    requiere_receta = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    detalle_compras = db.relationship('DetalleCompra', backref='producto', lazy=True)
    detalle_ventas = db.relationship('DetalleVenta', backref='producto', lazy=True)
    movimientos = db.relationship('MovimientoInventario', backref='producto', lazy=True)
    alertas = db.relationship('AlertaStock', backref='producto', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_producto,
            'codigo_barras': self.codigo_barras,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'marca': self.marca_ref.nombre if self.marca_ref else None,
            'categoria': self.categoria_ref.nombre if self.categoria_ref else None,
            'laboratorio': self.laboratorio_ref.nombre if self.laboratorio_ref else None,
            'presentacion': self.presentacion,
            'concentracion': self.concentracion,
            'precio_compra': float(self.precio_compra),
            'precio_venta': float(self.precio_venta),
            'stock_actual': self.stock_actual,
            'stock_minimo': self.stock_minimo,
            'stock_maximo': self.stock_maximo,
            'fecha_vencimiento': self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            'imagen_url': self.imagen_url,
            'requiere_receta': self.requiere_receta,
            'activo': self.activo
        }