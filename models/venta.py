from database.db import db
from datetime import datetime

class Venta(db.Model):
    __tablename__ = 'venta'
    
    id_venta = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    numero_venta = db.Column(db.String(20), unique=True, nullable=False)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    igv = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.String(20), default='COMPLETADA')
    observacion = db.Column(db.Text)
    
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', backref='ventas', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_venta,
            'numero': self.numero_venta,
            'fecha': self.fecha_venta.isoformat() if self.fecha_venta else None,
            'subtotal': float(self.subtotal),
            'igv': float(self.igv),
            'total': float(self.total),
            'metodo_pago': self.metodo_pago,
            'estado': self.estado,
            'usuario': self.usuario.nombre if self.usuario else None,
            'detalles': [d.to_dict() for d in self.detalles]
        }

class DetalleVenta(db.Model):
    __tablename__ = 'detalle_venta'
    
    id_detalle_venta = db.Column(db.Integer, primary_key=True)
    id_venta = db.Column(db.Integer, db.ForeignKey('venta.id_venta'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    descuento = db.Column(db.Numeric(10, 2), default=0)
    
    def to_dict(self):
        return {
            'id': self.id_detalle_venta,
            'producto': self.producto.nombre if self.producto else None,
            'producto_id': self.id_producto,
            'cantidad': self.cantidad,
            'precio_unitario': float(self.precio_unitario),
            'subtotal': float(self.subtotal),
            'descuento': float(self.descuento)
        }