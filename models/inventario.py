from database.db import db
from datetime import datetime

class TipoMovimiento(db.Model):
    __tablename__ = 'tipo_movimiento'
    
    id_tipo_movimiento = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    signo = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.Text)
    
    movimientos = db.relationship('MovimientoInventario', backref='tipo', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_tipo_movimiento,
            'nombre': self.nombre,
            'signo': self.signo,
            'descripcion': self.descripcion
        }

class MovimientoInventario(db.Model):
    __tablename__ = 'movimiento_inventario'
    
    id_movimiento = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    id_tipo_movimiento = db.Column(db.Integer, db.ForeignKey('tipo_movimiento.id_tipo_movimiento'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    stock_anterior = db.Column(db.Integer, nullable=False)
    stock_nuevo = db.Column(db.Integer, nullable=False)
    referencia_tabla = db.Column(db.String(50))
    referencia_id = db.Column(db.Integer)
    observacion = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuario', backref='movimientos', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_movimiento,
            'producto': self.producto.nombre if self.producto else None,
            'producto_id': self.id_producto,
            'usuario': self.usuario.nombre if self.usuario else None,
            'tipo': self.tipo.nombre if self.tipo else None,
            'cantidad': self.cantidad,
            'stock_anterior': self.stock_anterior,
            'stock_nuevo': self.stock_nuevo,
            'referencia': f"{self.referencia_tabla} #{self.referencia_id}" if self.referencia_tabla else None,
            'observacion': self.observacion,
            'fecha': self.fecha.isoformat() if self.fecha else None
        }

class AlertaStock(db.Model):
    __tablename__ = 'alerta_stock'
    
    id_alerta = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_lectura = db.Column(db.DateTime)
    estado = db.Column(db.String(20), default='PENDIENTE')
    id_usuario_atendio = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))
    fecha_atencion = db.Column(db.DateTime)
    
    usuario_atendio = db.relationship('Usuario', backref='alertas_atendidas', lazy=True, foreign_keys=[id_usuario_atendio])
    
    def to_dict(self):
        return {
            'id': self.id_alerta,
            'producto': self.producto.nombre if self.producto else None,
            'producto_id': self.id_producto,
            'tipo': self.tipo,
            'mensaje': self.mensaje,
            'fecha': self.fecha_generacion.isoformat() if self.fecha_generacion else None,
            'estado': self.estado
        }