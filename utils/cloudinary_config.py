import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Configurar Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def upload_image(file, folder='productos', public_id=None):
    """
    Sube una imagen a Cloudinary
    Args:
        file: Archivo de imagen (FileStorage o path)
        folder: Carpeta en Cloudinary (productos, detecciones, etc.)
        public_id: ID público personalizado (opcional)
    Returns:
        dict: Información de la imagen subida
    """
    try:
        # Si es un archivo de Flask
        if hasattr(file, 'filename'):
            # Subir desde archivo
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                public_id=public_id,
                use_filename=True,
                unique_filename=True,
                overwrite=True,
                resource_type='image'
            )
        else:
            # Subir desde ruta
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                public_id=public_id,
                use_filename=True,
                unique_filename=True,
                overwrite=True,
                resource_type='image'
            )
        
        return {
            'url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'width': result.get('width'),
            'height': result.get('height'),
            'format': result.get('format'),
            'bytes': result.get('bytes')
        }
        
    except Exception as e:
        print(f"Error al subir imagen a Cloudinary: {e}")
        return None

def upload_image_from_url(url, folder='productos', public_id=None):
    """
    Sube una imagen a Cloudinary desde una URL
    """
    try:
        result = cloudinary.uploader.upload(
            url,
            folder=folder,
            public_id=public_id,
            use_filename=True,
            unique_filename=True,
            overwrite=True,
            resource_type='image'
        )
        
        return {
            'url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'width': result.get('width'),
            'height': result.get('height'),
            'format': result.get('format'),
            'bytes': result.get('bytes')
        }
        
    except Exception as e:
        print(f"Error al subir imagen desde URL: {e}")
        return None

def upload_image_base64(image_base64, folder='productos', public_id=None):
    """
    Sube una imagen en base64 a Cloudinary
    """
    try:
        result = cloudinary.uploader.upload(
            f"data:image/jpeg;base64,{image_base64}",
            folder=folder,
            public_id=public_id,
            use_filename=True,
            unique_filename=True,
            overwrite=True,
            resource_type='image'
        )
        
        return {
            'url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'width': result.get('width'),
            'height': result.get('height'),
            'format': result.get('format'),
            'bytes': result.get('bytes')
        }
        
    except Exception as e:
        print(f"Error al subir imagen base64: {e}")
        return None

def delete_image(public_id):
    """
    Elimina una imagen de Cloudinary
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get('result') == 'ok'
    except Exception as e:
        print(f"Error al eliminar imagen: {e}")
        return False

def get_image_url(public_id, width=None, height=None, crop='limit', quality='auto'):
    """
    Obtiene la URL de una imagen con transformaciones
    """
    try:
        if width or height:
            transformation = {
                'width': width,
                'height': height,
                'crop': crop,
                'quality': quality
            }
            url = cloudinary.CloudinaryImage(public_id).build_url(**transformation)
        else:
            url = cloudinary.CloudinaryImage(public_id).build_url()
        
        return url
    except Exception as e:
        print(f"Error al obtener URL de imagen: {e}")
        return None

def list_images(folder='productos', max_results=100):
    """
    Lista las imágenes en una carpeta de Cloudinary
    """
    try:
        result = cloudinary.api.resources(
            type='upload',
            prefix=folder,
            max_results=max_results
        )
        return result.get('resources', [])
    except Exception as e:
        print(f"Error al listar imágenes: {e}")
        return []

def get_image_public_id_from_url(url):
    """
    Extrae el public_id de una URL de Cloudinary
    """
    try:
        # Ejemplo: https://res.cloudinary.com/dhhwmnnay/image/upload/v1234567890/productos/imagen.jpg
        parts = url.split('/')
        # Buscar la parte que contiene el public_id
        for i, part in enumerate(parts):
            if part in ['upload', 'image', 'video'] and i + 1 < len(parts):
                # El public_id está después de la versión
                if i + 2 < len(parts):
                    public_id_parts = parts[i+2:]
                    public_id = '/'.join(public_id_parts).split('.')[0]
                    return public_id
        return None
    except Exception as e:
        print(f"Error al extraer public_id: {e}")
        return None

# Función para generar miniaturas
def get_thumbnail_url(public_id, width=200, height=200):
    """
    Genera una URL de miniatura para una imagen
    """
    return get_image_url(public_id, width=width, height=height, crop='thumb')

# Función para generar imágenes optimizadas
def get_optimized_url(public_id, width=800):
    """
    Genera una URL optimizada para web
    """
    return get_image_url(public_id, width=width, crop='limit', quality='auto:good')

# Función para generar URL con marca de agua
def get_watermarked_url(public_id, watermark_public_id='watermark'):
    """
    Genera una URL con marca de agua
    """
    try:
        url = cloudinary.CloudinaryImage(public_id).build_url(
            transformation=[
                {'overlay': watermark_public_id},
                {'flags': 'relative', 'width': 0.3, 'crop': 'scale'},
                {'gravity': 'south_east', 'x': 10, 'y': 10}
            ]
        )
        return url
    except Exception as e:
        print(f"Error al generar URL con marca de agua: {e}")
        return None