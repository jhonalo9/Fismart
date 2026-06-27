from datetime import datetime
from models.producto import Producto
from models.venta import Venta
from models.ia import RecomendacionMensual, DetalleRecomendacion
from database.db import db
import random

def generar_numero_venta():
    """Genera un número de venta único"""
    fecha = datetime.now().strftime('%Y%m%d')
    count = Venta.query.filter(
        db.func.date(Venta.fecha_venta) == datetime.now().date()
    ).count()
    return f"VEN-{fecha}-{count + 1:04d}"

def calcular_total_venta(productos):
    """Calcula subtotal, IGV y total de una venta"""
    subtotal = 0
    for item in productos:
        subtotal += item['cantidad'] * item['precio_unitario']
    
    # Obtener porcentaje de IGV de configuración
    from models.configuracion import Configuracion
    config = Configuracion.query.filter_by(clave='igv_porcentaje').first()
    igv_porcentaje = float(config.valor) if config else 18.0
    
    igv = subtotal * (igv_porcentaje / 100)
    total = subtotal + igv
    
    return subtotal, igv, total

def simular_deteccion_ia(imagen_url):
    """Simula la detección de productos con IA (YOLO)"""
    # En un caso real, aquí se usaría YOLO para detectar productos
    # Esta es una simulación para demostración
    
    # Obtener algunos productos activos
    productos = Producto.query.filter_by(activo=True).limit(10).all()
    
    if not productos:
        return []
    
    # Simular detección de 1-5 productos
    num_detecciones = random.randint(1, min(5, len(productos)))
    productos_seleccionados = random.sample(productos, num_detecciones)
    
    detecciones = []
    for i, producto in enumerate(productos_seleccionados):
        detecciones.append({
            'id_producto': producto.id_producto,
            'nombre': producto.nombre,
            'cantidad': random.randint(1, 10),
            'confianza': round(random.uniform(70, 98), 2),
            'bbox_x': random.randint(10, 100),
            'bbox_y': random.randint(10, 100),
            'bbox_width': random.randint(50, 200),
            'bbox_height': random.randint(50, 200)
        })
    
    return detecciones

def generar_recomendaciones_mensuales(mes, anio, id_usuario):
    """Genera recomendaciones de compra basadas en ventas históricas"""
    from sqlalchemy import func
    
    # Crear la recomendación mensual
    recomendacion = RecomendacionMensual(
        mes=mes,
        anio=anio,
        estado='PENDIENTE'
    )
    db.session.add(recomendacion)
    db.session.flush()
    
    # Obtener productos con ventas en los últimos 3 meses
    fecha_inicio = datetime(anio, mes, 1)
    fecha_fin = datetime(anio, mes, 28)  # Aproximado
    
    productos = Producto.query.filter_by(activo=True).all()
    
    for producto in productos:
        # Calcular ventas promedio
        ventas = db.session.query(
            func.sum(DetalleVenta.cantidad)
        ).join(
            Venta, DetalleVenta.id_venta == Venta.id_venta
        ).filter(
            DetalleVenta.id_producto == producto.id_producto,
            Venta.fecha_venta >= fecha_inicio,
            Venta.fecha_venta <= fecha_fin,
            Venta.estado == 'COMPLETADA'
        ).scalar() or 0
        
        ventas_promedio = ventas / 3  # Promedio mensual de los últimos 3 meses
        
        # Si el stock está bajo, recomendar comprar
        if producto.stock_actual < producto.stock_minimo:
            cantidad_sugerida = max(
                producto.stock_maximo - producto.stock_actual,
                int(ventas_promedio * 1.5) - producto.stock_actual
            )
            
            if cantidad_sugerida > 0:
                detalle = DetalleRecomendacion(
                    id_recomendacion=recomendacion.id_recomendacion,
                    id_producto=producto.id_producto,
                    cantidad_sugerida=cantidad_sugerida,
                    stock_actual=producto.stock_actual,
                    ventas_promedio=ventas_promedio,
                    prioridad=1
                )
                db.session.add(detalle)
    
    db.session.commit()
    return recomendacion, recomendacion.detalles

def formatear_fecha(fecha):
    """Formatea una fecha para mostrar"""
    if fecha:
        return fecha.strftime('%d/%m/%Y %H:%M')
    return ''

def formatear_moneda(monto):
    """Formatea un monto en moneda"""
    if monto:
        return f'S/. {monto:,.2f}'
    return 'S/. 0.00'