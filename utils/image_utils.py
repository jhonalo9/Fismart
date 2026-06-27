from utils.cloudinary_config import get_image_url, get_thumbnail_url, get_optimized_url

def get_product_image_url(imagen_url, size='medium'):
    """
    Obtiene URL optimizada de producto según el tamaño
    """
    if not imagen_url:
        return None
    
    # Extraer public_id de la URL de Cloudinary
    from utils.cloudinary_config import get_image_public_id_from_url
    public_id = get_image_public_id_from_url(imagen_url)
    
    if not public_id:
        return imagen_url
    
    if size == 'thumbnail':
        return get_thumbnail_url(public_id, 100, 100)
    elif size == 'small':
        return get_thumbnail_url(public_id, 200, 200)
    elif size == 'medium':
        return get_optimized_url(public_id, 400)
    elif size == 'large':
        return get_optimized_url(public_id, 800)
    else:
        return imagen_url