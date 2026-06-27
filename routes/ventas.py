from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.venta import Venta, DetalleVenta
from models.producto import Producto
from database.db import db
from datetime import datetime

ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route('/')
@login_required
def listar():
    ventas = Venta.query.order_by(Venta.fecha_venta.desc()).all()
    return render_template('ventas/listar.html', ventas=ventas)

@ventas_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    if request.method == 'POST':
        # Procesar la venta
        productos_data = request.get_json()
        
        if not productos_data or 'productos' not in productos_data:
            return jsonify({'error': 'No se enviaron productos'}), 400
        
        try:
            from utils.helpers import calcular_total_venta, generar_numero_venta
            
            # Generar número de venta
            numero_venta = generar_numero_venta()
            
            # Calcular totales
            subtotal, igv, total = calcular_total_venta(productos_data['productos'])
            
            # Crear venta
            venta = Venta(
                id_usuario=current_user.id_usuario,
                numero_venta=numero_venta,
                subtotal=subtotal,
                igv=igv,
                total=total,
                metodo_pago=productos_data.get('metodo_pago', 'EFECTIVO'),
                observacion=productos_data.get('observacion')
            )
            
            db.session.add(venta)
            db.session.flush()
            
            # Crear detalles de venta
            for item in productos_data['productos']:
                producto = Producto.query.get(item['id_producto'])
                if not producto:
                    db.session.rollback()
                    return jsonify({'error': f'Producto {item["id_producto"]} no encontrado'}), 404
                
                if producto.stock_actual < item['cantidad']:
                    db.session.rollback()
                    return jsonify({'error': f'Stock insuficiente para {producto.nombre}'}), 400
                
                detalle = DetalleVenta(
                    id_venta=venta.id_venta,
                    id_producto=item['id_producto'],
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio_unitario'],
                    subtotal=item['cantidad'] * item['precio_unitario'],
                    descuento=item.get('descuento', 0)
                )
                db.session.add(detalle)
                
                # Actualizar stock
                producto.stock_actual -= item['cantidad']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'venta_id': venta.id_venta,
                'numero_venta': venta.numero_venta,
                'total': float(total),
                'message': 'Venta registrada exitosamente'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    # GET - Mostrar formulario
    productos = Producto.query.filter_by(activo=True).all()
    return render_template('ventas/nueva.html', productos=productos)

@ventas_bp.route('/<int:id>')
@login_required
def ver(id):
    venta = Venta.query.get_or_404(id)
    return render_template('ventas/ver.html', venta=venta)

@ventas_bp.route('/<int:id>/anular', methods=['POST'])
@login_required
def anular(id):
    venta = Venta.query.get_or_404(id)
    
    if venta.estado == 'CANCELADA':
        flash('La venta ya está anulada', 'warning')
        return redirect(url_for('ventas.ver', id=id))
    
    # Revertir stock
    for detalle in venta.detalles:
        producto = Producto.query.get(detalle.id_producto)
        if producto:
            producto.stock_actual += detalle.cantidad
    
    venta.estado = 'CANCELADA'
    db.session.commit()
    
    flash('Venta anulada exitosamente', 'success')
    return redirect(url_for('ventas.ver', id=id))

# API Endpoints
@ventas_bp.route('/api/ventas', methods=['GET'])
@login_required
def api_listar():
    ventas = Venta.query.order_by(Venta.fecha_venta.desc()).limit(100).all()
    return jsonify([v.to_dict() for v in ventas])

@ventas_bp.route('/api/ventas/<int:id>', methods=['GET'])
@login_required
def api_obtener(id):
    venta = Venta.query.get_or_404(id)
    return jsonify(venta.to_dict())

@ventas_bp.route('/api/ventas', methods=['POST'])
@login_required
def api_crear():
    data = request.get_json()
    
    if not data or 'productos' not in data:
        return jsonify({'error': 'No se enviaron productos'}), 400
    
    try:
        from utils.helpers import calcular_total_venta, generar_numero_venta
        
        numero_venta = generar_numero_venta()
        subtotal, igv, total = calcular_total_venta(data['productos'])
        
        venta = Venta(
            id_usuario=current_user.id_usuario,
            numero_venta=numero_venta,
            subtotal=subtotal,
            igv=igv,
            total=total,
            metodo_pago=data.get('metodo_pago', 'EFECTIVO'),
            observacion=data.get('observacion')
        )
        
        db.session.add(venta)
        db.session.flush()
        
        for item in data['productos']:
            producto = Producto.query.get(item['id_producto'])
            if not producto:
                db.session.rollback()
                return jsonify({'error': f'Producto {item["id_producto"]} no encontrado'}), 404
            
            if producto.stock_actual < item['cantidad']:
                db.session.rollback()
                return jsonify({'error': f'Stock insuficiente para {producto.nombre}'}), 400
            
            detalle = DetalleVenta(
                id_venta=venta.id_venta,
                id_producto=item['id_producto'],
                cantidad=item['cantidad'],
                precio_unitario=item['precio_unitario'],
                subtotal=item['cantidad'] * item['precio_unitario'],
                descuento=item.get('descuento', 0)
            )
            db.session.add(detalle)
            producto.stock_actual -= item['cantidad']
        
        db.session.commit()
        return jsonify(venta.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ventas_bp.route('/api/ventas/dia', methods=['GET'])
@login_required
def api_ventas_dia():
    from sqlalchemy import func
    
    hoy = datetime.now().date()
    ventas = Venta.query.filter(
        func.date(Venta.fecha_venta) == hoy,
        Venta.estado == 'COMPLETADA'
    ).all()
    
    total_ventas = len(ventas)
    total_monto = sum(v.total for v in ventas)
    
    return jsonify({
        'fecha': hoy.isoformat(),
        'total_ventas': total_ventas,
        'total_monto': float(total_monto),
        'ventas': [v.to_dict() for v in ventas]
    })