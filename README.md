# realtime-ocr-analyze

Registra contadores, medidores o cualquier número que cambie regularmente a lo largo del tiempo.

## Características

- Extrae los números de un contador cada X tiempo mediante OCR
- WebRTC para máximo rendimiento en dígitos muy variables (Sonómetros, Anemometros, etc), permitiendo capturar los dígitos un máximo de 5 a 10 veces por segundo
- Preprocesamiento y OCR en el servidor con Tesseract

## Funcionamiento

1. Des de un dispositivo con cámara, ir a /observer (https://IP_SERVIDOR/observer)
2. Empezar a grabar y encuadrar el contador dentro de la zona de interés (ROI)
3. El vídeo se transmite directamente al servidor por WebRTC
4. En el servidor se procesan las imágenes y se obtiene el número
5. 🔜 Guardar los datos en una base de datos temporal (InfluxDB)
6. 🔜 Mostrar datos y gràfico temporal a tiempo real

## Prerequisitos

1. **Python 3.8+**
2. **Tesseract OCR**
