import requests
from utils.ia_config import ia_model
import os

def test_deteccion():
    # Descargar una imagen de prueba (Panadol)
    url = "https://res.cloudinary.com/dhhwmnnay/image/upload/v1782516963/detecciones/imagen_cs7qvp.jpg"
    response = requests.get(url)
    
    if response.status_code == 200:
        with open("test_producto.jpg", "wb") as f:
            f.write(response.content)
        
        print("📸 Imagen descargada, probando detección...")
        
        # Probar detección
        resultado = ia_model.detectar_productos("test_producto.jpg")
        
        print(f"✅ Detecciones encontradas: {len(resultado)}")
        for det in resultado:
            print(f"   - {det['class']}: {det['confidence']:.2%}")
        
        # Limpiar
        os.remove("test_producto.jpg")
    else:
        print("❌ Error descargando imagen de prueba")

if __name__ == "__main__":
    test_deteccion()