from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from sqlalchemy import text

db = SQLAlchemy()

def init_db(app):
    """Inicializa la base de datos con la aplicación"""
    db.init_app(app)
    
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
        
        # Verificar y crear roles por defecto
        from models.usuario import Rol
        if Rol.query.count() == 0:
            roles_default = ['ADMIN', 'GERENTE', 'VENDEDOR', 'ALMACENERO', 'AUXILIAR']
            for rol in roles_default:
                db.session.add(Rol(nombre=rol))
            db.session.commit()
            
        # Verificar y crear tipos de movimiento
        from models.inventario import TipoMovimiento
        if TipoMovimiento.query.count() == 0:
            movimientos = [
                ('INGRESO_COMPRA', 1, 'Ingreso por compra a proveedor'),
                ('INGRESO_IA', 1, 'Ingreso por detección de IA'),
                ('SALIDA_VENTA', -1, 'Salida por venta'),
                ('SALIDA_AJUSTE', -1, 'Salida por ajuste de inventario'),
                ('INGRESO_AJUSTE', 1, 'Ingreso por ajuste de inventario'),
                ('SALIDA_VENCIMIENTO', -1, 'Salida por producto vencido'),
                ('INGRESO_DEVOLUCION', 1, 'Ingreso por devolución de cliente')
            ]
            for nombre, signo, descripcion in movimientos:
                db.session.add(TipoMovimiento(nombre=nombre, signo=signo, descripcion=descripcion))
            db.session.commit()
        
        # Crear usuario admin por defecto si no existe
        from models.usuario import Usuario
        if Usuario.query.filter_by(email='admin@botica.com').first() is None:
            admin = Usuario(
                nombre='Administrador',
                email='admin@botica.com',
                password='admin123',  # Se hasheará automáticamente
                id_rol=1
            )
            db.session.add(admin)
            db.session.commit()

def get_db():
    """Obtiene la conexión a la base de datos para consultas raw"""
    return db.session

def execute_raw_query(query, params=None):
    """Ejecuta una consulta SQL raw"""
    if params:
        result = db.session.execute(text(query), params)
    else:
        result = db.session.execute(text(query))
    db.session.commit()
    return result