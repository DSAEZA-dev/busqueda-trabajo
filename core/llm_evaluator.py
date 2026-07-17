import requests
import json
import time
from config.settings import OLLAMA_URL, MODEL_OLLAMA

def _call_ollama(prompt, fallback_data):
    payload = {
        "model": MODEL_OLLAMA, 
        "prompt": prompt,
        "format": "json",
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        result = json.loads(data["response"])
        result["is_simulated"] = False
        result["model_used"] = MODEL_OLLAMA
        return result
    except Exception:
        time.sleep(0.5)
        fallback_data["is_simulated"] = True
        fallback_data["model_used"] = "Simulación (Fallback)"
        return fallback_data

def evaluar_con_ollama(cv_text, job_desc, direccion_usuario, ubicacion_oferta, dias_antiguedad=0):
    prompt = f"""
    Eres un reclutador experto. Compara el CV con la oferta.
    
    CV DEL CANDIDATO:
    {cv_text}
    
    DESCRIPCIÓN DE LA OFERTA:
    {job_desc}
    
    ANTIGÜEDAD DE LA OFERTA:
    La oferta fue publicada hace {dias_antiguedad} días.
    Si la oferta tiene más de 30 días, es muy probable que esté inactiva. En ese caso, debes penalizar severamente el "puntaje" y mencionarlo explícitamente en "faltantes" o "consejo".
    
    Devuelve estrictamente un JSON (sin markdown adicional):
    {{
        "puntaje": 8,
        "pros": ["Puntos fuertes"],
        "faltantes": ["Habilidades que faltan o advertencia de antigüedad"],
        "consejo": "Consejo"
    }}
    """
    
    import random
    fallback = {
        "puntaje": random.choice([7, 8, 9, 10]),
        "pros": ["Perfil coincide parcialmente."],
        "faltantes": ["Podría faltar experiencia específica."],
        "consejo": "Destaca tus proyectos principales en el CV."
    }
    
    evaluacion = _call_ollama(prompt, fallback)
    
    # Comprobar cercanía geográfica
    cerca = False
    if direccion_usuario and ubicacion_oferta:
        # Una comprobación simple (se podría mejorar con NLP o APIs de mapas)
        dir_lower = direccion_usuario.lower()
        ubi_lower = ubicacion_oferta.lower()
        if dir_lower in ubi_lower or ubi_lower in dir_lower or "remoto" in ubi_lower:
            cerca = True
            
    evaluacion["cerca_de_casa"] = cerca
    return evaluacion

def analizar_perfil(cv_text):
    prompt = f"""
    Eres un analista de recursos humanos experto. Lee el siguiente CV y extrae:
    1. La profesión principal del candidato.
    2. La ubicación geográfica (región, ciudad o comuna) si se menciona en el CV. Si no se menciona, devuelve null.
    3. Una lista de 10 cargos afines a los que este candidato podría postular, junto con un porcentaje de afinidad para cada uno (de mayor a menor).
       IMPORTANTE: Si un cargo tiene un equivalente directo y común en inglés y español (por ejemplo: "Data Analyst" y "Analista de Datos"), debes AGRUPARLOS en un solo concepto separados por " / " (Ej: "Data Analyst / Analista de Datos"). No desperdicies 2 espacios de los 10 con el mismo cargo en distintos idiomas.
    4. Un "glosario_tecnico" basado ESTRICTAMENTE en las habilidades reales del CV. 
       - Extrae hasta 7 competencias clave.
       - Para cada competencia, genera 3 capas semánticas: "sinonimos", "herramientas" (o tecnologías/conceptos asociados REALES, inferibles del uso en el CV. NO inventes herramientas no relacionadas), e "impacto" (el valor aportado).
       - IMPORTANTE: Si el candidato menciona una herramienta con un fin específico (ej: "Python para análisis de datos"), NO la expandas con fines ajenos (ej: frameworks web como Django/FastAPI).

    REGLAS DE ORO: 
    - PROHIBIDO copiar el ejemplo de abajo. El ejemplo es de Gastronomía, el CV real es de otra profesión (Ingeniería, Salud, Administración, Informática, etc.).
    - Genera un resultado 100% fiel a la disciplina del CV provisto. No asumas que es del rubro informático si no lo dice explícitamente.

    CV:
    {cv_text}
    
    Devuelve estrictamente un JSON con esta estructura (EJEMPLO FICTICIO DE UN CHEF, NO LO COPIES):
    {{
        "profesion": "Chef Ejecutivo",
        "ubicacion": "Valparaíso",
        "cargos_sugeridos": [
            {{"cargo": "Chef de Cuisine / Jefe de Cocina", "afinidad": 95}},
            {{"cargo": "Sous Chef / Subchef", "afinidad": 85}}
        ],
        "glosario_tecnico": {{
            "Cocina Francesa": {{
                "sinonimos": ["Gastronomía clásica", "Haute cuisine"],
                "herramientas": ["Sous-vide", "Sifón", "Cuchillería especializada"],
                "impacto": ["Menús de degustación", "Excelencia culinaria"]
            }}
        }}
    }}
    """
    
    fallback = {
        "profesion": "No detectada (IA no disponible)",
        "ubicacion": "No detectada",
        "cargos_sugeridos": [],
        "glosario_tecnico": {},
        "fallback_reason": "El servidor de IA local no respondió. El análisis no pudo completarse. Revisa que Ollama esté ejecutándose e inténtalo de nuevo."
    }
    
    return _call_ollama(prompt, fallback)

def generar_cv_latex(cv_text, profesion_objetivo):
    prompt = f"""
    Eres un experto en currículums ATS-friendly. Convierte el siguiente texto de un CV en código LaTeX puro (estilo Jake's Resume), optimizado específicamente para postular a cargos de "{profesion_objetivo}".
    
    El CV debe verse profesional. Escapa correctamente caracteres especiales de LaTeX si es necesario.
    
    CV ORIGINAL:
    {cv_text}
    
    Devuelve estrictamente un JSON con una sola llave "latex_code" que contenga TODO el código LaTeX en formato string:
    {{
        "latex_code": "\\\\documentclass{{article}}..."
    }}
    """
    
    fallback_latex = "% Simulación de CV en LaTeX\n\\documentclass[letterpaper,11pt]{article}\n\\begin{document}\n\\textbf{CV Optimizado (Demo)}\n\\end{document}"
    
    fallback = {"latex_code": fallback_latex}
    resultado = _call_ollama(prompt, fallback)
    return resultado.get("latex_code", fallback_latex)

def mejorar_redaccion_cv(cv_text):
    prompt = f"""
    Eres un experto en empleabilidad y redacción de currículums ATS-friendly.
    Tu objetivo es tomar el texto bruto de un currículum y reescribirlo para que suene mucho más profesional e impactante.
    
    Reglas:
    - Usa verbos de acción fuertes y lenguaje orientado a logros.
    - Mantén la verdad de los datos: NO inventes experiencia, cargos ni herramientas que no estén.
    - Corrige errores ortográficos y de redacción.
    - Devuelve la información estructurada claramente en formato texto/markdown ligero.
    
    TEXTO BRUTO DEL CV:
    {cv_text}
    
    Devuelve estrictamente un JSON con una sola llave "cv_mejorado" que contenga el texto completo mejorado.
    {{
        "cv_mejorado": "Tu texto mejorado aquí..."
    }}
    """
    
    fallback = {
        "cv_mejorado": cv_text + "\n\n(Error: La IA local no pudo procesar la mejora. Se mantiene el original.)"
    }
    
    resultado = _call_ollama(prompt, fallback)
    return resultado.get("cv_mejorado", fallback["cv_mejorado"])

def parsear_cv_a_json(cv_text):
    prompt = f"""
    Eres un parser experto de currículums. Toma el siguiente texto bruto de un CV y conviértelo en un JSON estructurado.
    
    Reglas IMPORTANTES:
    - Extrae la información con máxima precisión. No omitas partes. El "resumen" debe ser TODO el párrafo o párrafos de introducción del candidato.
    - Si no encuentras información para un campo, devuelve una cadena vacía "". NUNCA devuelvas `null`.
    - En la sección "logros", debes unir todas las viñetas y descripciones de ese cargo en un solo bloque de texto. NO devuelvas una lista.
    - Para las habilidades, únelas en una sola cadena separada por comas (ej: "Python, Excel, Liderazgo"). NO devuelvas una lista/array.
    
    TEXTO BRUTO DEL CV:
    {cv_text}
    
    Devuelve estrictamente un JSON con esta estructura exacta (SIN MARKDOWN ADICIONAL):
    {{
        "titular": "...",
        "resumen": "...",
        "experiencias": [
            {{"cargo": "...", "empresa": "...", "fechas": "...", "logros": "..."}}
        ],
        "cursos": [
            {{"nombre": "...", "institucion": "..."}}
        ],
        "habilidades": "..."
    }}
    """
    
    fallback = {
        "titular": "",
        "resumen": "",
        "experiencias": [],
        "cursos": [],
        "habilidades": ""
    }
    
    import json
    try:
        resultado = _call_ollama(prompt, fallback)
        return resultado
    except Exception:
        return fallback
