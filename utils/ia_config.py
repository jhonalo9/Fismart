import os
from inference_sdk import InferenceHTTPClient
import cv2
import numpy as np
from PIL import Image
import io
import base64

class IAModel:
    def __init__(self):
        self.api_url = "https://serverless.roboflow.com"
        self.api_key = "z9YpeiBDiW1XeVCMm7Jb"
        self.model_id = "pharmacy-gx0v4/2"
        self.client = InferenceHTTPClient(
            api_url=self.api_url,
            api_key=self.api_key
        )
        self.confidence_threshold = 0.5  # Ajusta según tu modelo
    
    def detectar_productos(self, imagen_path):
        """
        Detecta productos en una imagen
        Args:
            imagen_path: Ruta de la imagen o URL
        Returns:
            Lista de detecciones con: nombre, confianza, bbox, etc.
        """
        try:
            
            if not os.path.exists(imagen_path):
                print(f"❌ La imagen no existe: {imagen_path}")
                return []
            
            # 🔥 VERIFICAR QUE LA IMAGEN NO ESTÉ VACÍA
            if os.path.getsize(imagen_path) == 0:
                print(f"❌ La imagen está vacía: {imagen_path}")
                return []
            
            # 🔥 VERIFICAR QUE LA IMAGEN SEA VÁLIDA CON OpenCV
            img = cv2.imread(imagen_path)
            if img is None:
                print(f"❌ No se pudo leer la imagen: {imagen_path}")
                return []
            
            print(f"✅ Imagen cargada: {imagen_path} ({img.shape})")
            # Realizar la inferencia
            result = self.client.infer(imagen_path, model_id=self.model_id)
            
            # Procesar los resultados
            detecciones = []
            
            if 'predictions' in result:
                for pred in result['predictions']:
                    # Verificar confianza
                    if pred.get('confidence', 0) >= self.confidence_threshold:
                        deteccion = {
                            'class': pred.get('class', 'desconocido'),
                            'confidence': pred.get('confidence', 0),
                            'bbox': {
                                'x': pred.get('x', 0),
                                'y': pred.get('y', 0),
                                'width': pred.get('width', 0),
                                'height': pred.get('height', 0)
                            }
                        }
                        detecciones.append(deteccion)
            
            return detecciones
            
        except Exception as e:
            print(f"Error en la detección: {e}")
            return []
    
    def detectar_desde_archivo(self, archivo):
        """
        Detecta productos desde un archivo subido
        Args:
            archivo: Archivo de imagen (FileStorage)
        Returns:
            Lista de detecciones
        """
        try:
            # Guardar temporalmente la imagen
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                archivo.save(tmp.name)
                tmp_path = tmp.name
            
            # Realizar detección
            detecciones = self.detectar_productos(tmp_path)
            
            # Eliminar archivo temporal
            os.unlink(tmp_path)
            
            return detecciones
            
        except Exception as e:
            print(f"Error al procesar archivo: {e}")
            return []
    
    def detectar_desde_base64(self, imagen_base64):
        """
        Detecta productos desde una imagen en base64
        """
        try:
            # Decodificar base64
            import tempfile
            import os
            
            # Decodificar imagen
            imagen_data = base64.b64decode(imagen_base64)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(imagen_data)
                tmp_path = tmp.name
            
            # Realizar detección
            detecciones = self.detectar_productos(tmp_path)
            
            # Eliminar archivo temporal
            os.unlink(tmp_path)
            
            return detecciones
            
        except Exception as e:
            print(f"Error al procesar base64: {e}")
            return []

# Instancia global
ia_model = IAModel()