from database.db import db
from datetime import datetime

class IngresoIA(db.Model):
    __tablename__ = 'ingreso_ia'
    
    id_ingreso = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))
    imagen_url = db.Column(db.String(255), nullable=False)
    fecha_deteccion = db.Column(db.DateTime, default=datetime.utcnow)
    procesado = db.Column(db.Boolean, default=False)
    validado = db.Column(db.Boolean, default=False)
    observacion = db.Column(db.Text)
    
    detalles = db.relationship('DetalleIngresoIA', backref='ingreso', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', backref='ingresos_ia', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_ingreso,
            'imagen': self.imagen_url,
            'fecha': self.fecha_deteccion.isoformat() if self.fecha_deteccion else None,
            'procesado': self.procesado,
            'validado': self.validado,
            'usuario': self.usuario.nombre if self.usuario else None,
            'detalles': [d.to_dict() for d in self.detalles]
        }

class DetalleIngresoIA(db.Model):
    __tablename__ = 'detalle_ingreso_ia'
    
    id_detalle_ingreso = db.Column(db.Integer, primary_key=True)
    id_ingreso = db.Column(db.Integer, db.ForeignKey('ingreso_ia.id_ingreso'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    cantidad_detectada = db.Column(db.Integer, nullable=False)
    cantidad_validada = db.Column(db.Integer)
    confianza = db.Column(db.Numeric(5, 2), nullable=False)
    bbox_x = db.Column(db.Integer)
    bbox_y = db.Column(db.Integer)
    bbox_width = db.Column(db.Integer)
    bbox_height = db.Column(db.Integer)
    validado = db.Column(db.Boolean, default=False)
    fecha_validacion = db.Column(db.DateTime)
    
    producto = db.relationship('Producto', backref='detecciones_ia', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_detalle_ingreso,
            'producto': self.producto.nombre if self.producto else None,
            'producto_id': self.id_producto,
            'cantidad_detectada': self.cantidad_detectada,
            'cantidad_validada': self.cantidad_validada,
            'confianza': float(self.confianza),
            'validado': self.validado,
            'bbox': {
                'x': self.bbox_x,
                'y': self.bbox_y,
                'width': self.bbox_width,
                'height': self.bbox_height
            } if self.bbox_x else None
        }

class RecomendacionMensual(db.Model):
    __tablename__ = 'recomendacion_mensual'
    
    id_recomendacion = db.Column(db.Integer, primary_key=True)
    mes = db.Column(db.Integer, nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='PENDIENTE')
    id_usuario_aprobacion = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))
    fecha_aprobacion = db.Column(db.DateTime)
    observacion = db.Column(db.Text)
    
    detalles = db.relationship('DetalleRecomendacion', backref='recomendacion', lazy=True, cascade='all, delete-orphan')
    usuario_aprobacion = db.relationship('Usuario', backref='recomendaciones_aprobadas', lazy=True, foreign_keys=[id_usuario_aprobacion])
    
    def to_dict(self):
        return {
            'id': self.id_recomendacion,
            'mes': self.mes,
            'anio': self.anio,
            'fecha': self.fecha_generacion.isoformat() if self.fecha_generacion else None,
            'estado': self.estado,
            'detalles': [d.to_dict() for d in self.detalles]
        }

class DetalleRecomendacion(db.Model):
    __tablename__ = 'detalle_recomendacion'
    
    id_detalle_recomendacion = db.Column(db.Integer, primary_key=True)
    id_recomendacion = db.Column(db.Integer, db.ForeignKey('recomendacion_mensual.id_recomendacion'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    cantidad_sugerida = db.Column(db.Integer, nullable=False)
    stock_actual = db.Column(db.Integer, nullable=False)
    ventas_promedio = db.Column(db.Numeric(10, 2))
    prioridad = db.Column(db.Integer, default=1)
    
    producto = db.relationship('Producto', backref='recomendaciones', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id_detalle_recomendacion,
            'producto': self.producto.nombre if self.producto else None,
            'producto_id': self.id_producto,
            'cantidad_sugerida': self.cantidad_sugerida,
            'stock_actual': self.stock_actual,
            'ventas_promedio': float(self.ventas_promedio) if self.ventas_promedio else None,
            'prioridad': self.prioridad
        }