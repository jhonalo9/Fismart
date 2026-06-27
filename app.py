from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from database.db import init_db, db
from models.usuario import Usuario
import os
from datetime import timedelta

# Inicializar la aplicación
app = Flask(__name__)
app.config.from_object(Config)

# Configurar CORS
CORS(app)

# Inicializar base de datos
init_db(app)

# Configurar Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Registrar blueprints
from routes.auth import auth_bp
from routes.productos import productos_bp
from routes.ventas import ventas_bp
from routes.compras import compras_bp
from routes.inventario import inventario_bp
from routes.ia import ia_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(productos_bp, url_prefix='/productos')
app.register_blueprint(ventas_bp, url_prefix='/ventas')
app.register_blueprint(compras_bp, url_prefix='/compras')
app.register_blueprint(inventario_bp, url_prefix='/inventario')
app.register_blueprint(ia_bp, url_prefix='/ia')

# Rutas principales
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', user=current_user)
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Obtener datos para el dashboard
    from models.producto import Producto
    from models.venta import Venta
    from models.inventario import AlertaStock
    
    total_productos = Producto.query.filter_by(activo=True).count()
    productos_bajo_stock = Producto.query.filter(Producto.stock_actual <= Producto.stock_minimo, Producto.activo == True).count()
    ventas_hoy = Venta.query.filter(db.func.date(Venta.fecha_venta) == db.func.date(db.func.now())).count()
    alertas_pendientes = AlertaStock.query.filter_by(estado='PENDIENTE').count()
    
    # Productos con poco stock
    productos_criticos = Producto.query.filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.activo == True
    ).limit(10).all()
    
    # Últimas ventas
    ultimas_ventas = Venta.query.order_by(Venta.fecha_venta.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_productos=total_productos,
                         productos_bajo_stock=productos_bajo_stock,
                         ventas_hoy=ventas_hoy,
                         alertas_pendientes=alertas_pendientes,
                         productos_criticos=productos_criticos,
                         ultimas_ventas=ultimas_ventas,
                         user=current_user)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Context processors para templates
@app.context_processor
def utility_processor():
    def format_date(date):
        if date:
            return date.strftime('%d/%m/%Y %H:%M')
        return ''
    
    def format_currency(amount):
        if amount:
            return f'S/. {amount:,.2f}'
        return 'S/. 0.00'
    
    return dict(format_date=format_date, format_currency=format_currency)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    
@app.context_processor
def inject_user():
    from flask_login import current_user
    return dict(user=current_user)