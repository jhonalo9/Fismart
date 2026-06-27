from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models.ia import IngresoIA, DetalleIngresoIA, RecomendacionMensual, DetalleRecomendacion
from models.producto import Producto
from models.inventario import MovimientoInventario
from database.db import db
from datetime import datetime
from utils.helpers import generar_recomendaciones_mensuales
from utils.ia_config import ia_model
from utils.cloudinary_config import upload_image, get_image_url, delete_image, upload_image_base64
from utils.busqueda_productos import buscar_producto_inteligente, buscar_productos_similares # 🔥 NUEVO IMPORT
import base64
import json
import os
import tempfile

ia_bp = Blueprint('ia', __name__)

@ia_bp.route('/deteccion')
@login_required
def deteccion():
    return render_template('ia/deteccion.html')

@ia_bp.route('/api/deteccion', methods=['POST'])
@login_required
def api_deteccion():
    try:
        imagen_url = None
        detecciones = []
        
        # Verificar si se envió un archivo
        if 'imagen' in request.files:
            archivo = request.files['imagen']
            
            # 🔥 VERIFICAR QUE HAYA UN ARCHIVO
            if archivo.filename == '':
                return jsonify({'error': 'No se seleccionó ninguna imagen'}), 400
            
            # 🔥 VERIFICAR EL TAMAÑO DEL ARCHIVO
            archivo.seek(0, 2)  # Ir al final
            tamaño = archivo.tell()
            archivo.seek(0)  # Volver al inicio
            
            print(f"📸 Tamaño del archivo: {tamaño} bytes")
            
            if tamaño == 0:
                return jsonify({'error': 'El archivo de imagen está vacío (0 bytes)'}), 400
            
            # 🔥 GUARDAR EL ARCHIVO CON UN NOMBRE ÚNICO
            import uuid
            nombre_archivo = f"detection_{uuid.uuid4().hex}.jpg"
            ruta_guardado = os.path.join('static', 'temp', nombre_archivo)
            
            # Crear carpeta temporal si no existe
            os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
            
            # Guardar archivo
            archivo.save(ruta_guardado)
            
            # 🔥 VERIFICAR QUE SE GUARDÓ CORRECTAMENTE
            if not os.path.exists(ruta_guardado) or os.path.getsize(ruta_guardado) == 0:
                return jsonify({'error': 'Error al guardar la imagen'}), 400
            
            print(f"✅ Imagen guardada en: {ruta_guardado} ({os.path.getsize(ruta_guardado)} bytes)")
            
            # Subir a Cloudinary
            try:
                resultado_cloud = upload_image(ruta_guardado, folder='detecciones')
                if resultado_cloud:
                    imagen_url = resultado_cloud['url']
                    print(f"✅ Imagen subida a Cloudinary: {imagen_url}")
            except Exception as e:
                print(f"⚠️ Error subiendo a Cloudinary: {e}")
                # Continuar aunque falle Cloudinary
            
            # Realizar detección con la ruta guardada
            try:
                detecciones = ia_model.detectar_productos(ruta_guardado)
                print(f"📊 Detecciones encontradas: {len(detecciones)}")
            except Exception as e:
                print(f"❌ Error en detección: {e}")
                # Limpiar archivo temporal
                if os.path.exists(ruta_guardado):
                    os.remove(ruta_guardado)
                return jsonify({'error': f'Error en detección: {str(e)}'}), 500
            
            # Eliminar archivo temporal después de la detección
            if os.path.exists(ruta_guardado):
                os.remove(ruta_guardado)
                print(f"🧹 Archivo temporal eliminado: {ruta_guardado}")
            
        elif request.is_json:
            data = request.get_json()
            if not data or 'imagen' not in data:
                return jsonify({'error': 'No se envió la imagen'}), 400
            
            imagen_base64 = data['imagen']
            if not imagen_base64 or len(imagen_base64) < 100:
                return jsonify({'error': 'La imagen base64 está vacía o es inválida'}), 400
            
            # Subir imagen base64 a Cloudinary
            try:
                from utils.cloudinary_config import upload_image_base64
                resultado_cloud = upload_image_base64(imagen_base64, folder='detecciones')
                if resultado_cloud:
                    imagen_url = resultado_cloud['url']
            except Exception as e:
                print(f"⚠️ Error subiendo a Cloudinary: {e}")
            
            # Realizar detección
            detecciones = ia_model.detectar_desde_base64(imagen_base64)
        else:
            return jsonify({'error': 'Formato de imagen no soportado'}), 400
        
        # 🔥 SI NO HAY DETECCIONES, DEVOLVER MENSAJE CLARO
        if not detecciones:
            return jsonify({
                'success': True,
                'total_detectados': 0,
                'total_actualizados': 0,
                'total_no_encontrados': 0,
                'mensaje': 'No se detectaron productos en la imagen. Prueba con otra imagen más clara.',
                'actualizados': [],
                'no_encontrados': []
            })
        
        # 🔥 OBTENER TODOS LOS PRODUCTOS UNA SOLA VEZ (CACHÉ)
        productos_cache = Producto.query.filter_by(activo=True).all()
        
        # Procesar detecciones y mapear a productos usando búsqueda inteligente
        productos_detectados = []
        productos_no_encontrados = []
        productos_actualizados = []
        
        for deteccion in detecciones:
            clase = deteccion.get('class', '')
            confianza = deteccion.get('confidence', 0)
            cantidad = 1  # Por defecto 1, se puede mejorar
            
            # 🔍 BUSCAR PRODUCTO CON BÚSQUEDA INTELIGENTE
            producto_encontrado, metodo = buscar_producto_inteligente(clase, productos_cache)
            
            if producto_encontrado:
                # ✅ PRODUCTO ENCONTRADO - Actualizar stock
                stock_anterior = producto_encontrado.stock_actual
                producto_encontrado.stock_actual += cantidad
                
                # Registrar movimiento en inventario
                movimiento = MovimientoInventario(
                    id_producto=producto_encontrado.id_producto,
                    id_usuario=current_user.id_usuario,
                    id_tipo_movimiento=2,  # INGRESO_IA
                    cantidad=cantidad,
                    stock_anterior=stock_anterior,
                    stock_nuevo=producto_encontrado.stock_actual,
                    observacion=f'✅ IA: {clase} → {producto_encontrado.nombre} (conf: {confianza:.0%}, método: {metodo})'
                )
                db.session.add(movimiento)
                
                productos_actualizados.append({
                    'id_producto': producto_encontrado.id_producto,
                    'nombre': producto_encontrado.nombre,
                    'stock_anterior': stock_anterior,
                    'stock_nuevo': producto_encontrado.stock_actual,
                    'cantidad': cantidad,
                    'confianza': confianza,
                    'clase_ia': clase,
                    'metodo_mapeo': metodo
                })
            else:
                # ❌ PRODUCTO NO ENCONTRADO
                
                sugerencias = buscar_productos_similares(clase, productos_cache, limite=3)

                productos_no_encontrados.append({
                    'clase_ia': clase,
                    'confianza': confianza,
                    'metodo_mapeo': metodo,
                    'sugerencias': [
                        {
                            'id': s['producto'].id_producto,
                            'nombre': s['producto'].nombre,
                            'similitud': f"{s['similitud']:.0%}"
                        }
                        for s in sugerencias
                    ]
                })
        
        # Guardar en la base de datos
        ingreso = IngresoIA(
            id_usuario=current_user.id_usuario,
            imagen_url=imagen_url,
            procesado=True,
            validado=False
        )
        db.session.add(ingreso)
        db.session.flush()
        
        # Guardar detalles de productos encontrados y no encontrados
        for det in productos_actualizados:
            detalle = DetalleIngresoIA(
                id_ingreso=ingreso.id_ingreso,
                id_producto=det.get('id_producto'),
                cantidad_detectada=det.get('cantidad', 1),
                cantidad_validada=det.get('cantidad', 1),
                confianza=det.get('confianza', 0),
                bbox_x=None,
                bbox_y=None,
                bbox_width=None,
                bbox_height=None,
                validado=True
            )
            db.session.add(detalle)
        
        for det in productos_no_encontrados:
            detalle = DetalleIngresoIA(
                id_ingreso=ingreso.id_ingreso,
                id_producto=None,
                cantidad_detectada=1,
                cantidad_validada=0,
                confianza=det.get('confianza', 0),
                bbox_x=None,
                bbox_y=None,
                bbox_width=None,
                bbox_height=None,
                validado=False
            )
            db.session.add(detalle)
        
        db.session.commit()
        
        # 📊 PREPARAR RESPUESTA
        return jsonify({
            'success': True,
            'ingreso_id': ingreso.id_ingreso,
            'imagen_url': imagen_url,
            'total_detectados': len(detecciones),
            'total_actualizados': len(productos_actualizados),
            'total_no_encontrados': len(productos_no_encontrados),
            'actualizados': productos_actualizados,
            'no_encontrados': productos_no_encontrados,
            'mensaje': f'✅ {len(productos_actualizados)} productos actualizados. ❌ {len(productos_no_encontrados)} no encontrados.'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en detección: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ... (el resto de las rutas de IA igual) ...


@ia_bp.route('/recomendaciones')
@login_required
def recomendaciones():
    """Página de recomendaciones de IA"""
    recomendaciones = RecomendacionMensual.query.order_by(
        RecomendacionMensual.anio.desc(),
        RecomendacionMensual.mes.desc()
    ).all()
    return render_template('ia/recomendaciones.html', recomendaciones=recomendaciones)

@ia_bp.route('/recomendaciones/generar', methods=['POST'])
@login_required
def generar_recomendaciones():
    """Genera recomendaciones de compra mensuales"""
    if not current_user.is_gerente():
        flash('No tienes permisos para generar recomendaciones', 'danger')
        return redirect(url_for('ia.recomendaciones'))
    
    try:
        from utils.helpers import generar_recomendaciones_mensuales
        
        mes = datetime.now().month
        anio = datetime.now().year
        
        # Verificar si ya existen recomendaciones para este mes
        existente = RecomendacionMensual.query.filter_by(mes=mes, anio=anio).first()
        if existente:
            flash('Ya existen recomendaciones para este mes', 'warning')
            return redirect(url_for('ia.recomendaciones'))
        
        # Generar recomendaciones
        recomendacion, detalles = generar_recomendaciones_mensuales(mes, anio, current_user.id_usuario)
        
        flash(f'Recomendaciones generadas exitosamente. {len(detalles)} productos recomendados.', 'success')
        return redirect(url_for('ia.recomendaciones'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al generar recomendaciones: {str(e)}', 'danger')
        return redirect(url_for('ia.recomendaciones'))

@ia_bp.route('/recomendaciones/<int:id>/aprobar', methods=['POST'])
@login_required
def aprobar_recomendacion(id):
    """Aprobar una recomendación"""
    if not current_user.is_gerente():
        return jsonify({'error': 'No tienes permisos'}), 403
    
    recomendacion = RecomendacionMensual.query.get_or_404(id)
    recomendacion.estado = 'APROBADA'
    recomendacion.id_usuario_aprobacion = current_user.id_usuario
    recomendacion.fecha_aprobacion = datetime.utcnow()
    
    db.session.commit()
    flash('Recomendación aprobada exitosamente', 'success')
    return redirect(url_for('ia.recomendaciones'))

@ia_bp.route('/recomendaciones/<int:id>/rechazar', methods=['POST'])
@login_required
def rechazar_recomendacion(id):
    """Rechazar una recomendación"""
    if not current_user.is_gerente():
        return jsonify({'error': 'No tienes permisos'}), 403
    
    recomendacion = RecomendacionMensual.query.get_or_404(id)
    recomendacion.estado = 'RECHAZADA'
    recomendacion.id_usuario_aprobacion = current_user.id_usuario
    recomendacion.fecha_aprobacion = datetime.utcnow()
    
    db.session.commit()
    flash('Recomendación rechazada', 'info')
    return redirect(url_for('ia.recomendaciones'))

@ia_bp.route('/api/recomendaciones/<int:id>', methods=['GET'])
@login_required
def api_recomendacion_detalle(id):
    """Obtener detalle de una recomendación"""
    recomendacion = RecomendacionMensual.query.get_or_404(id)
    return jsonify(recomendacion.to_dict())



@ia_bp.route('/api/deteccion/<int:id>', methods=['GET'])
@login_required
def api_detalle_deteccion(id):
    """Obtiene el detalle de una detección"""
    try:
        ingreso = IngresoIA.query.get(id)
        
        if not ingreso:
            return jsonify({'error': 'Detección no encontrada'}), 404
        
        # Obtener detalles
        detalles = DetalleIngresoIA.query.filter_by(id_ingreso=id).all()
        
        # Construir respuesta
        lista_detalles = []
        for detalle in detalles:
            producto_nombre = detalle.producto.nombre if detalle.producto else None
            lista_detalles.append({
                'id': detalle.id_detalle_ingreso,
                'producto': producto_nombre,
                'producto_id': detalle.id_producto,
                'cantidad_detectada': detalle.cantidad_detectada,
                'cantidad_validada': detalle.cantidad_validada,
                'confianza': float(detalle.confianza) if detalle.confianza else 0,
                'validado': detalle.validado
            })
        
        return jsonify({
            'id': ingreso.id_ingreso,
            'fecha': ingreso.fecha_deteccion.isoformat() if ingreso.fecha_deteccion else None,
            'imagen': ingreso.imagen_url,
            'validado': ingreso.validado,
            'procesado': ingreso.procesado,
            'usuario': ingreso.usuario.nombre if ingreso.usuario else 'Sistema',
            'detalles': lista_detalles
        })
        
    except Exception as e:
        print(f"❌ Error en detalle: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500



@ia_bp.route('/api/deteccion/historial', methods=['GET'])
@login_required
def api_historial():
    """Obtiene el historial de detecciones"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        # Obtener ingresos con sus detalles
        ingresos = IngresoIA.query.order_by(
            IngresoIA.fecha_deteccion.desc()
        ).limit(limit).all()
        
        # Convertir a diccionario manejando posibles errores
        resultado = []
        for ingreso in ingresos:
            try:
                # Obtener detalles
                detalles = DetalleIngresoIA.query.filter_by(
                    id_ingreso=ingreso.id_ingreso
                ).all()
                
                lista_detalles = []
                
                for detalle in detalles:
                    nombre_producto = detalle.producto.nombre if detalle.producto else 'No mapeado'
                    lista_detalles.append({
                        'id': detalle.id_detalle_ingreso,
                        'producto': nombre_producto,
                        'producto_id': detalle.id_producto,
                        'cantidad_detectada': detalle.cantidad_detectada,
                        'cantidad_validada': detalle.cantidad_validada,
                        'confianza': float(detalle.confianza) if detalle.confianza else 0,
                        'validado': detalle.validado
                    })
                
                resultado.append({
                    'id': ingreso.id_ingreso,
                    'fecha': ingreso.fecha_deteccion.isoformat() if ingreso.fecha_deteccion else None,
                    'imagen': ingreso.imagen_url,
                    'validado': ingreso.validado,
                    'procesado': ingreso.procesado,
                    'detalles': lista_detalles,  # ← AHORA ES UN ARRAY
                    'total_detalles': len(lista_detalles),
                    'productos_mapeados': sum(1 for d in lista_detalles if d['producto_id'] is not None),
                    'usuario': ingreso.usuario.nombre if ingreso.usuario else 'Sistema'
                })
            except Exception as e:
                print(f"Error procesando ingreso {ingreso.id_ingreso}: {e}")
                continue
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Error en api_historial: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500