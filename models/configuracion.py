from database.db import db
from datetime import datetime

class Configuracion(db.Model):
    __tablename__ = 'configuracion'
    
    id_configuracion = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.Text)
    tipo = db.Column(db.String(20))
    descripcion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id_configuracion,
            'clave': self.clave,
            'valor': self.valor,
            'tipo': self.tipo,
            'descripcion': self.descripcion
        }