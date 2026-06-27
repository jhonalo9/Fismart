from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.inventario import MovimientoInventario, AlertaStock
from models.producto import Producto
from database.db import db

inventario_bp = Blueprint('inventario', __name__)

@inventario_bp.route('/movimientos')
@login_required
def movimientos():
    movimientos = MovimientoInventario.query.order_by(
        MovimientoInventario.fecha.desc()
    ).limit(100).all()
    return render_template('inventario/movimientos.html', movimientos=movimientos)

@inventario_bp.route('/stock')
@login_required
def stock():
    productos = Producto.query.filter_by(activo=True).all()
    alertas = AlertaStock.query.filter_by(estado='PENDIENTE').all()
    return render_template('inventario/stock.html', productos=productos, alertas=alertas)

@inventario_bp.route('/alertas/<int:id>/marcar_leida', methods=['POST'])
@login_required
def marcar_alerta_leida(id):
    alerta = AlertaStock.query.get_or_404(id)
    alerta.estado = 'LEIDA'
    alerta.fecha_lectura = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@inventario_bp.route('/alertas/<int:id>/atender', methods=['POST'])
@login_required
def atender_alerta(id):
    alerta = AlertaStock.query.get_or_404(id)
    alerta.estado = 'ATENDIDA'
    alerta.id_usuario_atendio = current_user.id_usuario
    alerta.fecha_atencion = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

# API Endpoints
@inventario_bp.route('/api/movimientos', methods=['GET'])
@login_required
def api_movimientos():
    limit = request.args.get('limit', 50, type=int)
    producto_id = request.args.get('producto_id', type=int)
    
    query = MovimientoInventario.query
    if producto_id:
        query = query.filter_by(id_producto=producto_id)
    
    movimientos = query.order_by(
        MovimientoInventario.fecha.desc()
    ).limit(limit).all()
    
    return jsonify([m.to_dict() for m in movimientos])

@inventario_bp.route('/api/alertas', methods=['GET'])
@login_required
def api_alertas():
    estado = request.args.get('estado', 'PENDIENTE')
    alertas = AlertaStock.query.filter_by(estado=estado).all()
    return jsonify([a.to_dict() for a in alertas])

@inventario_bp.route('/api/stock/bajo', methods=['GET'])
@login_required
def api_stock_bajo():
    productos = Producto.query.filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.activo == True
    ).all()
    return jsonify([p.to_dict() for p in productos])