from difflib import SequenceMatcher
from database.db import db
from models.producto import Producto
import re

def limpiar_texto(texto):
    """
    Limpia el texto para mejor comparación
    - Elimina acentos
    - Convierte a minúsculas
    - Elimina caracteres especiales
    """
    if not texto:
        return ""
    
    texto = texto.lower().strip()
    
    # Reemplazar acentos
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u'
    }
    for acento, normal in reemplazos.items():
        texto = texto.replace(acento, normal)
    
    # Eliminar caracteres especiales (solo letras, números y espacios)
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    
    return texto

def buscar_producto_inteligente(clase_ia, productos_cache=None):
    """
    Busca un producto en la BD usando SOLO la base de datos
    SIN diccionarios manuales
    """
    if not clase_ia:
        return None, 'error_vacio'
    
    # Limpiar el texto de la IA
    clase_ia_limpia = limpiar_texto(clase_ia)
    
    # Obtener productos cache
    if productos_cache is None:
        productos_cache = Producto.query.filter_by(activo=True).all()
    
    # 🔥 1. MAPEO POR NOMBRE EXACTO (sin diccionario)
    for p in productos_cache:
        nombre_limpio = limpiar_texto(p.nombre)
        if nombre_limpio == clase_ia_limpia:
            return p, f'exacto: {clase_ia} = {p.nombre}'
    
    # 🔥 2. MAPEO POR CONTENIDO (la clase está en el nombre del producto)
    for p in productos_cache:
        nombre_limpio = limpiar_texto(p.nombre)
        if clase_ia_limpia in nombre_limpio:
            return p, f'contiene: {clase_ia} in {p.nombre}'
    
    # 🔥 3. MAPEO POR CONTENIDO INVERSO (el nombre del producto está en la clase)
    for p in productos_cache:
        nombre_limpio = limpiar_texto(p.nombre)
        if nombre_limpio in clase_ia_limpia:
            return p, f'contenido_inverso: {p.nombre} in {clase_ia}'
    
    # 🔥 4. MAPEO POR PALABRAS CLAVE (más inteligente)
    palabras_clave = clase_ia_limpia.split()
    for p in productos_cache:
        nombre_limpio = limpiar_texto(p.nombre)
        # Contar cuántas palabras coinciden
        coincidencias = 0
        for palabra in palabras_clave:
            if len(palabra) > 2:  # Ignorar palabras muy cortas
                if palabra in nombre_limpio:
                    coincidencias += 1
        
        # Si más del 50% de las palabras coinciden
        if len(palabras_clave) > 0 and coincidencias / len(palabras_clave) >= 0.5:
            return p, f'palabras_clave: {coincidencias}/{len(palabras_clave)} coinciden'
    
    # 🔥 5. MAPEO POR SIMILITUD DE TEXTO (fuzzy matching)
    mejor_producto = None
    mejor_puntaje = 0
    umbral = 0.6  # 60% de similitud mínimo
    
    for p in productos_cache:
        nombre_limpio = limpiar_texto(p.nombre)
        
        # Calcular similitud
        similitud = SequenceMatcher(
            None, 
            clase_ia_limpia, 
            nombre_limpio
        ).ratio()
        
        if similitud > mejor_puntaje and similitud >= umbral:
            mejor_puntaje = similitud
            mejor_producto = p
    
    if mejor_producto:
        return mejor_producto, f'similitud: {mejor_puntaje:.0%}'
    
    # 🔥 6. MAPEO POR CÓDIGO DE BARRAS (si la clase parece un código)
    if len(clase_ia) >= 8 and clase_ia.isdigit():
        for p in productos_cache:
            if p.codigo_barras and p.codigo_barras == clase_ia:
                return p, f'codigo_barras: {clase_ia}'
    
    # 🔥 7. MAPEO POR CATEGORÍA (último recurso)
    # Si la clase coincide con el nombre de una categoría
    from models.producto import Categoria
    categorias = Categoria.query.all()
    for cat in categorias:
        if clase_ia_limpia in limpiar_texto(cat.nombre):
            # Buscar cualquier producto de esa categoría
            for p in productos_cache:
                if p.id_categoria == cat.id_categoria:
                    return p, f'categoria: {cat.nombre}'
    
    # ❌ No encontrado
    return None, f'no_encontrado: {clase_ia}'

def buscar_productos_similares(clase_ia, productos_cache=None, limite=5):
    """
    Busca productos similares para sugerir cuando no se encuentra exacto
    """
    if not clase_ia:
        return []
    
    clase_ia_limpia = limpiar_texto(clase_ia)
    
    if productos_cache is None:
        productos_cache = Producto.query.filter_by(activo=True).all()
    
    # Calcular similitud con todos los productos
    resultados = []
    for p in productos_cache:
        nombre_limpio = limpiar_texto(p.nombre)
        similitud = SequenceMatcher(
            None, 
            clase_ia_limpia, 
            nombre_limpio
        ).ratio()
        
        if similitud > 0.3:  # Más del 30% de similitud
            resultados.append({
                'producto': p,
                'similitud': similitud
            })
    
    # Ordenar por similitud (mayor a menor)
    resultados.sort(key=lambda x: x['similitud'], reverse=True)
    
    return resultados[:limite]