from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.producto import Producto, Categoria, Marca, Laboratorio
from database.db import db
from datetime import datetime
from utils.cloudinary_config import upload_image, delete_image, get_image_url

productos_bp = Blueprint('productos', __name__)

@productos_bp.route('/')
@login_required
def listar():
    productos = Producto.query.filter_by(activo=True).all()
    return render_template('productos/listar.html', productos=productos)

@productos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        try:
            # Procesar imagen si se subió
            imagen_url = None
            if 'imagen' in request.files:
                archivo = request.files['imagen']
                if archivo.filename != '':
                    # Subir a Cloudinary
                    resultado = upload_image(archivo, folder='productos')
                    if resultado:
                        imagen_url = resultado['url']
            
            producto = Producto(
                codigo_barras=request.form.get('codigo_barras'),
                nombre=request.form.get('nombre'),
                descripcion=request.form.get('descripcion'),
                id_marca=request.form.get('id_marca') or None,
                id_categoria=request.form.get('id_categoria') or None,
                id_laboratorio=request.form.get('id_laboratorio') or None,
                presentacion=request.form.get('presentacion'),
                concentracion=request.form.get('concentracion'),
                precio_compra=float(request.form.get('precio_compra')),
                precio_venta=float(request.form.get('precio_venta')),
                stock_actual=int(request.form.get('stock_actual') or 0),
                stock_minimo=int(request.form.get('stock_minimo') or 5),
                stock_maximo=int(request.form.get('stock_maximo') or 100),
                requiere_receta=bool(request.form.get('requiere_receta')),
                imagen_url=imagen_url
            )
            
            # Fecha de vencimiento
            fecha_vencimiento = request.form.get('fecha_vencimiento')
            if fecha_vencimiento:
                producto.fecha_vencimiento = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
            
            db.session.add(producto)
            db.session.commit()
            
            flash('Producto creado exitosamente', 'success')
            return redirect(url_for('productos.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear producto: {str(e)}', 'danger')
            return redirect(url_for('productos.crear'))
    
    categorias = Categoria.query.all()
    marcas = Marca.query.all()
    laboratorios = Laboratorio.query.all()
    
    return render_template('productos/crear.html', 
                         categorias=categorias, 
                         marcas=marcas, 
                         laboratorios=laboratorios)

@productos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    producto = Producto.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Procesar nueva imagen si se subió
            if 'imagen' in request.files:
                archivo = request.files['imagen']
                if archivo.filename != '':
                    # Eliminar imagen anterior si existe
                    if producto.imagen_url:
                        # Extraer public_id y eliminar
                        from utils.cloudinary_config import get_image_public_id_from_url, delete_image
                        public_id = get_image_public_id_from_url(producto.imagen_url)
                        if public_id:
                            delete_image(public_id)
                    
                    # Subir nueva imagen
                    resultado = upload_image(archivo, folder='productos')
                    if resultado:
                        producto.imagen_url = resultado['url']
            
            producto.codigo_barras = request.form.get('codigo_barras')
            producto.nombre = request.form.get('nombre')
            producto.descripcion = request.form.get('descripcion')
            producto.id_marca = request.form.get('id_marca') or None
            producto.id_categoria = request.form.get('id_categoria') or None
            producto.id_laboratorio = request.form.get('id_laboratorio') or None
            producto.presentacion = request.form.get('presentacion')
            producto.concentracion = request.form.get('concentracion')
            producto.precio_compra = float(request.form.get('precio_compra'))
            producto.precio_venta = float(request.form.get('precio_venta'))
            producto.stock_minimo = int(request.form.get('stock_minimo') or 5)
            producto.stock_maximo = int(request.form.get('stock_maximo') or 100)
            producto.requiere_receta = bool(request.form.get('requiere_receta'))
            producto.activo = bool(request.form.get('activo'))
            
            fecha_vencimiento = request.form.get('fecha_vencimiento')
            if fecha_vencimiento:
                producto.fecha_vencimiento = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
            else:
                producto.fecha_vencimiento = None
            
            db.session.commit()
            flash('Producto actualizado exitosamente', 'success')
            return redirect(url_for('productos.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {str(e)}', 'danger')
            return redirect(url_for('productos.editar', id=id))
    
    categorias = Categoria.query.all()
    marcas = Marca.query.all()
    laboratorios = Laboratorio.query.all()
    
    return render_template('productos/editar.html', 
                         producto=producto,
                         categorias=categorias, 
                         marcas=marcas, 
                         laboratorios=laboratorios)

@productos_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    try:
        producto = Producto.query.get_or_404(id)
        
        # Eliminar imagen de Cloudinary
        if producto.imagen_url:
            from utils.cloudinary_config import get_image_public_id_from_url, delete_image
            public_id = get_image_public_id_from_url(producto.imagen_url)
            if public_id:
                delete_image(public_id)
        
        producto.activo = False
        db.session.commit()
        flash('Producto desactivado exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desactivar producto: {str(e)}', 'danger')
    
    return redirect(url_for('productos.listar'))