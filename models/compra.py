from database.db import db
from datetime import datetime

class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    
    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ruc = db.Column(db.String(20), unique=True)
    direccion = db.Column(db.Text)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    contacto_nombre = db.Column(db.String(100))
    contacto_telefono = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    compras = db.relationship('Compra', backref='proveedor', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_proveedor,
            'nombre': self.nombre,
            'ruc': self.ruc,
            'telefono': self.telefono,
            'email': self.email,
            'contacto': self.contacto_nombre,
            'activo': self.activo
        }

class Compra(db.Model):
    __tablename__ = 'compra'
    
    id_compra = db.Column(db.Integer, primary_key=True)
    id_proveedor = db.Column(db.Integer, db.ForeignKey('proveedor.id_proveedor'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    numero_factura = db.Column(db.String(50), unique=True)
    fecha_compra = db.Column(db.Date, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    igv = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.String(20), default='PENDIENTE')
    observacion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    detalles = db.relationship('DetalleCompra', backref='compra', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', backref='compras', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_compra,
            'numero_factura': self.numero_factura,
            'fecha': self.fecha_compra.isoformat() if self.fecha_compra else None,
            'proveedor': self.proveedor.nombre if self.proveedor else None,
            'subtotal': float(self.subtotal),
            'igv': float(self.igv),
            'total': float(self.total),
            'estado': self.estado,
            'detalles': [d.to_dict() for d in self.detalles]
        }

class DetalleCompra(db.Model):
    __tablename__ = 'detalle_compra'
    
    id_detalle_compra = db.Column(db.Integer, primary_key=True)
    id_compra = db.Column(db.Integer, db.ForeignKey('compra.id_compra'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_vencimiento = db.Column(db.Date)
    lote = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'id': self.id_detalle_compra,
            'producto': self.producto.nombre if self.producto else None,
            'producto_id': self.id_producto,
            'cantidad': self.cantidad,
            'precio_unitario': float(self.precio_unitario),
            'subtotal': float(self.subtotal),
            'fecha_vencimiento': self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            'lote': self.lote
        }