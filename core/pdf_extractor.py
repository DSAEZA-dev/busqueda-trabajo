import fitz  # PyMuPDF
import easyocr
import numpy as np

# Inicializamos el reader de forma global pero diferida para no penalizar el inicio de la app
_reader = None

def get_ocr_reader():
    global _reader
    if _reader is None:
        # Inicializa EasyOCR para español e inglés. gpu=True intentará usar CUDA si está disponible
        _reader = easyocr.Reader(['es', 'en'], gpu=True)
    return _reader

def extraer_texto_pdf(file_bytes: bytes, ocr_threshold: int = 100) -> str:
    """
    Extrae texto de un archivo PDF dado en bytes.
    Primero intenta extracción directa. Si el texto resultante tiene menos 
    caracteres que `ocr_threshold`, aplica OCR a las páginas mediante EasyOCR.
    """
    # Cargar documento desde memoria
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    
    # Intento 1: Extracción directa
    texto_extraido = ""
    for page in doc:
        texto_extraido += page.get_text() + "\n"
        
    texto_limpio = texto_extraido.strip()
    
    # Validación: ¿Es probablemente un documento escaneado?
    if len(texto_limpio) >= ocr_threshold:
        return texto_limpio
        
    # Intento 2: Fallback a OCR (EasyOCR)
    texto_ocr = ""
    reader = get_ocr_reader()
    
    for page in doc:
        # Convertir página a imagen. Usamos zoom 2x para mejorar la resolución y precisión del OCR
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        
        # Convertir Pixmap a array de numpy (formato BGR o RGB)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        
        # Si tiene canal alfa (RGBA), descartarlo
        if pix.n == 4:
            img_array = img_array[:, :, :3]
            
        # Ejecutar OCR (detail=0 devuelve solo la lista de strings detectados)
        resultados = reader.readtext(img_array, detail=0)
        texto_ocr += " ".join(resultados) + "\n"
        
    return texto_ocr.strip()
