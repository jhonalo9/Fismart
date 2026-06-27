from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.compra import Compra, DetalleCompra, Proveedor
from models.producto import Producto
from models.configuracion import Configuracion
from database.db import db
from datetime import datetime

# Crear el Blueprint
compras_bp = Blueprint('compras', __name__)

@compras_bp.route('/')
@login_required
def listar():
    compras = Compra.query.order_by(Compra.fecha_compra.desc()).all()
    return render_template('compras/listar.html', compras=compras)

@compras_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    if request.method == 'POST':
        try:
            proveedor_id = request.form.get('id_proveedor')
            fecha_compra = request.form.get('fecha_compra')
            numero_factura = request.form.get('numero_factura')
            productos_data = request.get_json()
            
            if not productos_data or 'productos' not in productos_data:
                flash('No se enviaron productos', 'danger')
                return redirect(url_for('compras.nueva'))
            
            # Calcular totales
            subtotal = 0
            for item in productos_data['productos']:
                subtotal += item['cantidad'] * item['precio_unitario']
            
            # Calcular IGV
            config = Configuracion.query.filter_by(clave='igv_porcentaje').first()
            igv_porcentaje = float(config.valor) if config else 18.0
            igv = subtotal * (igv_porcentaje / 100)
            total = subtotal + igv
            
            # Crear compra
            compra = Compra(
                id_proveedor=proveedor_id,
                id_usuario=current_user.id_usuario,
                numero_factura=numero_factura,
                fecha_compra=datetime.strptime(fecha_compra, '%Y-%m-%d').date(),
                subtotal=subtotal,
                igv=igv,
                total=total,
                observacion=request.form.get('observacion')
            )
            
            db.session.add(compra)
            db.session.flush()
            
            # Crear detalles de compra
            for item in productos_data['productos']:
                detalle = DetalleCompra(
                    id_compra=compra.id_compra,
                    id_producto=item['id_producto'],
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio_unitario'],
                    subtotal=item['cantidad'] * item['precio_unitario'],
                    lote=item.get('lote')
                )
                
                # Fecha de vencimiento
                if item.get('fecha_vencimiento'):
                    detalle.fecha_vencimiento = datetime.strptime(item['fecha_vencimiento'], '%Y-%m-%d').date()
                
                db.session.add(detalle)
            
            db.session.commit()
            
            flash('Compra registrada exitosamente', 'success')
            return redirect(url_for('compras.ver', id=compra.id_compra))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar la compra: {str(e)}', 'danger')
            return redirect(url_for('compras.nueva'))
    
    proveedores = Proveedor.query.filter_by(activo=True).all()
    productos = Producto.query.filter_by(activo=True).all()
    return render_template('compras/nueva.html', proveedores=proveedores, productos=productos)

@compras_bp.route('/<int:id>')
@login_required
def ver(id):
    compra = Compra.query.get_or_404(id)
    return render_template('compras/ver.html', compra=compra)

# API Endpoints
@compras_bp.route('/api/proveedores', methods=['GET'])
@login_required
def api_proveedores():
    proveedores = Proveedor.query.filter_by(activo=True).all()
    return jsonify([p.to_dict() for p in proveedores])

@compras_bp.route('/api/proveedores', methods=['POST'])
@login_required
def api_crear_proveedor():
    data = request.get_json()
    
    proveedor = Proveedor(
        nombre=data.get('nombre'),
        ruc=data.get('ruc'),
        direccion=data.get('direccion'),
        telefono=data.get('telefono'),
        email=data.get('email'),
        contacto_nombre=data.get('contacto_nombre'),
        contacto_telefono=data.get('contacto_telefono')
    )
    
    db.session.add(proveedor)
    db.session.commit()
    
    return jsonify(proveedor.to_dict()), 201

@compras_bp.route('/api/compras', methods=['GET'])
@login_required
def api_listar():
    compras = Compra.query.order_by(Compra.fecha_compra.desc()).limit(50).all()
    return jsonify([c.to_dict() for c in compras])

@compras_bp.route('/api/compras', methods=['POST'])
@login_required
def api_crear_compra():
    data = request.get_json()
    
    try:
        subtotal = sum(item['cantidad'] * item['precio_unitario'] for item in data['productos'])
        config = Configuracion.query.filter_by(clave='igv_porcentaje').first()
        igv_porcentaje = float(config.valor) if config else 18.0
        igv = subtotal * (igv_porcentaje / 100)
        total = subtotal + igv
        
        compra = Compra(
            id_proveedor=data['id_proveedor'],
            id_usuario=current_user.id_usuario,
            numero_factura=data.get('numero_factura'),
            fecha_compra=datetime.strptime(data['fecha_compra'], '%Y-%m-%d').date(),
            subtotal=subtotal,
            igv=igv,
            total=total,
            observacion=data.get('observacion')
        )
        
        db.session.add(compra)
        db.session.flush()
        
        for item in data['productos']:
            detalle = DetalleCompra(
                id_compra=compra.id_compra,
                id_producto=item['id_producto'],
                cantidad=item['cantidad'],
                precio_unitario=item['precio_unitario'],
                subtotal=item['cantidad'] * item['precio_unitario'],
                lote=item.get('lote')
            )
            db.session.add(detalle)
        
        db.session.commit()
        return jsonify(compra.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500