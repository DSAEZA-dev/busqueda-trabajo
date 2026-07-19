import requests
import json
import base64
import os
import tempfile
import subprocess
import time
from config.settings import OLLAMA_URL, MODEL_OLLAMA

def compilar_latex_pdf(latex_code):
    """Compila código LaTeX a PDF usando pdflatex del sistema (MiKTeX).
    Ejecuta pdflatex dos veces para resolver referencias cruzadas.
    Retorna los bytes del PDF o None si falla."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "cv.tex")
            pdf_path = os.path.join(tmpdir, "cv.pdf")
            
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(latex_code)
            
            # Ejecutar pdflatex dos veces (para resolver referencias)
            for i in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, tex_path],
                    capture_output=True, text=True, timeout=60, cwd=tmpdir
                )
            
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    return f.read()
            else:
                # Mostrar las últimas líneas del log para debug
                log_path = os.path.join(tmpdir, "cv.log")
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                        log_content = f.read()
                    # Extraer solo las líneas de error
                    errores = [l for l in log_content.split("\n") if l.startswith("!") or "Error" in l]
                    if errores:
                        print(f"Errores LaTeX: {'; '.join(errores[:5])}")
                print(f"pdflatex stderr: {result.stderr[-500:] if result.stderr else 'N/A'}")
                return None
    except subprocess.TimeoutExpired:
        print("Error: pdflatex tardó más de 60 segundos.")
        return None
    except FileNotFoundError:
        print("Error: pdflatex no está instalado. Instala MiKTeX desde https://miktex.org/")
        return None
    except Exception as e:
        print(f"Error compilando PDF: {e}")
        return None

MODEL_VISION = "llava"

def _call_ollama(prompt, fallback_data):
    payload = {
        "model": MODEL_OLLAMA, 
        "prompt": prompt,
        "format": "json",
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
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

def _call_ollama_vision(prompt, image_bytes, fallback_data):
    """Llama a Ollama con un modelo de visión (llava) para procesar imágenes."""
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    payload = {
        "model": MODEL_VISION,
        "prompt": prompt,
        "images": [image_b64],
        "format": "json",
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        result = json.loads(data["response"])
        result["is_simulated"] = False
        result["model_used"] = MODEL_VISION
        return result
    except Exception:
        time.sleep(0.5)
        fallback_data["is_simulated"] = True
        fallback_data["model_used"] = "Simulación (Fallback)"
        return fallback_data

def mejorar_campo_con_ia(texto_campo, tipo_campo):
    """Mejora un campo individual del CV con IA."""
    instrucciones = {
        "resumen": "Reescribe este resumen profesional para que sea más impactante, conciso y orientado a logros. Usa verbos de acción y lenguaje ejecutivo.",
        "logros": "Reescribe estos logros laborales para que suenen más profesionales e impactantes. Usa verbos de acción fuertes, cuantifica resultados cuando sea posible y destaca el valor aportado.",
        "aprendizajes": "Reescribe estas competencias y aprendizajes adquiridos de forma profesional, enfatizando las habilidades técnicas y blandas ganadas y su aplicabilidad.",
        "habilidades": "Reorganiza y mejora esta lista de habilidades para que sea más clara y profesional. Agrupa por categorías si es posible (técnicas, blandas, herramientas). Devuelve como texto separado por comas."
    }
    
    instruccion = instrucciones.get(tipo_campo, "Mejora este texto para que sea más profesional e impactante.")
    
    prompt = f"""
    {instruccion}
    
    Reglas:
    - Mantén la VERDAD de los datos: NO inventes información que no esté presente.
    - Corrige errores ortográficos y de redacción.
    - El resultado debe estar en español.
    
    TEXTO ORIGINAL:
    {texto_campo}
    
    Devuelve estrictamente un JSON con una sola llave "texto_mejorado":
    {{
        "texto_mejorado": "Tu texto mejorado aquí..."
    }}
    """
    
    fallback = {"texto_mejorado": texto_campo}
    resultado = _call_ollama(prompt, fallback)
    return resultado.get("texto_mejorado", texto_campo)

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

def analizar_perfil(cv_text, cargos_descartados=None):
    if cargos_descartados is None: cargos_descartados = []
    
    exclusion_text = ""
    if cargos_descartados:
        exclusion_text = f"\n    ESTRICTAMENTE PROHIBIDO SUGERIR ESTOS CARGOS (El usuario ya los descartó): {', '.join(cargos_descartados)}\n"
        
    prompt = f"""
    Eres un analista de recursos humanos experto. Lee el siguiente CV y extrae:
    1. La profesión principal del candidato.
    2. La ubicación geográfica (región, ciudad o comuna) si se menciona en el CV. Si no se menciona, devuelve null.
    3. Una lista de 10 cargos afines a los que este candidato podría postular, junto con un porcentaje de afinidad para cada uno (de mayor a menor).
       IMPORTANTE: Si un cargo tiene un equivalente directo y común en inglés y español (por ejemplo: "Data Analyst" y "Analista de Datos"), debes AGRUPARLOS en un solo concepto separados por " / " (Ej: "Data Analyst / Analista de Datos"). No desperdicies 2 espacios de los 10 con el mismo cargo en distintos idiomas.
       Además, para cada cargo, incluye un campo "habilidad_faltante_clave" indicando 1 o 2 tecnologías, herramientas o conocimientos puntuales que el candidato debería aprender para mejorar su % de afinidad con el estándar del mercado.
    4. Un cálculo de "seniority_por_dominio". Agrupa la experiencia del CV en distintas "áreas profesionales" detectadas (ej: "Desarrollo Backend", "Soporte TI", "Ventas") y calcula los años totales de experiencia y el nivel (Trainee, Junior, Mid-Level, Senior, Lead) específicamente para cada área.
    5. Un "glosario_tecnico" basado ESTRICTAMENTE en las habilidades reales del CV. 
       - Extrae hasta 7 competencias clave.
       - Para cada competencia, genera 3 capas semánticas: "sinonimos", "herramientas" (o tecnologías/conceptos asociados REALES, inferibles del uso en el CV. NO inventes herramientas no relacionadas), e "impacto" (el valor aportado).
       - IMPORTANTE: Si el candidato menciona una herramienta con un fin específico (ej: "Python para análisis de datos"), NO la expandas con fines ajenos (ej: frameworks web como Django/FastAPI).
{exclusion_text}
    REGLAS DE ORO: 
    - PROHIBIDO copiar el ejemplo de abajo. El ejemplo es de Gastronomía, el CV real es de otra profesión (Ingeniería, Salud, Administración, Informática, etc.).
    - Genera un resultado 100% fiel a la disciplina del CV provisto. No asumas que es del rubro informático si no lo dice explícitamente.

    CV:
    {cv_text}
    
    Devuelve estrictamente un JSON con esta estructura (EJEMPLO FICTICIO DE UN CHEF, NO LO COPIES):
    {{
        "profesion": "Chef Ejecutivo",
        "ubicacion": "Valparaíso",
        "seniority_por_dominio": {{
            "Alta Cocina": {{"años": 8, "nivel": "Senior"}},
            "Administración Gastronómica": {{"años": 3, "nivel": "Mid-Level"}}
        }},
        "cargos_sugeridos": [
            {{"cargo": "Chef de Cuisine / Jefe de Cocina", "afinidad": 95, "habilidad_faltante_clave": "Certificación en seguridad alimentaria ISO 22000"}},
            {{"cargo": "Sous Chef / Subchef", "afinidad": 85, "habilidad_faltante_clave": "Manejo de software de inventario (ej. ChefTec)"}}
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
        "seniority_por_dominio": {},
        "cargos_sugeridos": [],
        "glosario_tecnico": {},
        "fallback_reason": "El servidor de IA local no respondió. El análisis no pudo completarse. Revisa que Ollama esté ejecutándose e inténtalo de nuevo."
    }
    
    return _call_ollama(prompt, fallback)

def generar_cv_latex(cv_text, profesion_objetivo):
    prompt = f"""
    Eres un experto en currículums ATS-friendly. Convierte el siguiente texto de un CV en código LaTeX puro (estilo Jake's Resume), optimizado específicamente para postular a cargos de "{profesion_objetivo}".
    
    INSTRUCCIONES CLAVE DE OPTIMIZACIÓN (CLUSTERING):
    - Debes reestructurar el CV original enfocándote EXCLUSIVAMENTE en hacer match con el perfil de "{profesion_objetivo}".
    - Reordena las habilidades, poniendo primero las que sean más relevantes para este rol.
    - Resalta y expande los logros que aporten directamente a este nicho.
    - Minimiza (o resume brevemente) la experiencia pasada que no aporte valor a este dominio específico.
    - El CV debe verse profesional. Escapa correctamente caracteres especiales de LaTeX si es necesario.
    
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

def generar_cv_latex_para_oferta(cv_text, descripcion_oferta, profesion_objetivo):
    prompt = f"""
    Eres un experto en currículums ATS-friendly. Convierte el siguiente texto de un CV en código LaTeX puro (estilo Jake's Resume), 
    optimizado específicamente para postular a esta oferta de empleo. 
    
    Ajusta el resumen, destaca los logros más relevantes para esta oferta y reescribe los puntos de experiencia y habilidades para 
    hacer el mayor "match" posible con la descripción de la oferta, SIN INVENTAR experiencia que no esté en el CV original.
    
    OFERTA DE EMPLEO ({profesion_objetivo}):
    {descripcion_oferta}
    
    CV ORIGINAL:
    {cv_text}
    
    Devuelve estrictamente un JSON con una sola llave "latex_code" que contenga TODO el código LaTeX en formato string:
    {{
        "latex_code": "\\\\documentclass{{article}}..."
    }}
    """
    
    fallback_latex = "% Simulación de CV en LaTeX (Para Oferta)\n\\documentclass[letterpaper,11pt]{article}\n\\begin{document}\n\\textbf{CV Optimizado para Oferta (Demo)}\n\\end{document}"
    
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
    - Extrae la información con máxima precisión. No omitas partes.
    - "nombre" es el nombre completo de la persona (Ej: "Juan Pérez González"). NO confundir con el título profesional.
    - "titulo" es el título o rol profesional (Ej: "Ingeniero Civil Industrial", "Analista de Datos").
    - El "resumen" debe ser TODO el párrafo o párrafos de introducción/perfil del candidato.
    - Si no encuentras información para un campo, devuelve una cadena vacía "". NUNCA devuelvas `null`.
    - En la sección "logros", debes unir todas las viñetas y descripciones de ese cargo en un solo bloque de texto. NO devuelvas una lista.
    - En la sección "aprendizajes", extrae las competencias, tecnologías o habilidades que el candidato adquirió o desarrolló en ese cargo. Si no se mencionan explícitamente, infiere las más probables de la descripción. NO devuelvas una lista.
    - Para los cursos, incluye el campo "fechas" con el período de estudio (Ej: "2020 - 2024"). Si no se menciona, devuelve una cadena vacía.
    - Para las habilidades técnicas, únelas en una sola cadena separada por comas (ej: "Python, Excel, SQL"). NO devuelvas una lista/array.
    - Para las habilidades blandas, únelas en una sola cadena separada por comas (ej: "Liderazgo, Trabajo en equipo, Comunicación efectiva"). NO devuelvas una lista/array. Si no se mencionan explícitamente, infiere las más probables del contexto del CV.
    
    TEXTO BRUTO DEL CV:
    {cv_text}
    
    Devuelve estrictamente un JSON con esta estructura exacta (SIN MARKDOWN ADICIONAL):
    {{
        "nombre": "...",
        "titulo": "...",
        "resumen": "...",
        "experiencias": [
            {{"cargo": "...", "empresa": "...", "fechas": "...", "logros": "...", "aprendizajes": "..."}}
        ],
        "cursos": [
            {{"nombre": "...", "institucion": "...", "fechas": "..."}}
        ],
        "habilidades": "...",
        "habilidades_blandas": "..."
    }}
    """
    
    fallback = {
        "nombre": "",
        "titulo": "",
        "resumen": "",
        "experiencias": [],
        "cursos": [],
        "habilidades": "",
        "habilidades_blandas": ""
    }
    
    try:
        resultado = _call_ollama(prompt, fallback)
        return resultado
    except Exception:
        return fallback

def generar_cv_desde_imagen(image_bytes, cv_text):
    """Genera código LaTeX basado en una imagen de referencia de diseño de CV y los datos del usuario."""
    prompt = f"""
    Eres un experto en diseño de currículums y LaTeX.
    
    Analiza la imagen adjunta que es un prototipo/diseño de referencia de un currículum.
    Tu tarea es generar código LaTeX COMPLETO que replique lo más fielmente posible el DISEÑO VISUAL de la imagen (disposición, columnas, secciones, tipografía, colores), pero utilizando los DATOS REALES del candidato que se proporcionan abajo.
    
    DATOS REALES DEL CANDIDATO (usar estos, NO los de la imagen):
    {cv_text}
    
    Reglas:
    - El código LaTeX debe compilar correctamente sin errores.
    - Replica el diseño visual de la imagen: layout, columnas, orden de secciones, uso de íconos si los hay.
    - Escapa caracteres especiales de LaTeX correctamente.
    - Usa paquetes estándar (geometry, fontawesome5, xcolor, tikz, tabularx, etc.).
    
    Devuelve estrictamente un JSON con una sola llave "latex_code":
    {{
        "latex_code": "\\\\documentclass{{article}}..."
    }}
    """
    
    fallback_latex = "% Error: No se pudo procesar la imagen\n\\documentclass[letterpaper,11pt]{article}\n\\begin{document}\n\\textbf{Error al generar CV desde imagen}\n\\end{document}"
    fallback = {"latex_code": fallback_latex}
    
    resultado = _call_ollama_vision(prompt, image_bytes, fallback)
    return resultado.get("latex_code", fallback_latex)
