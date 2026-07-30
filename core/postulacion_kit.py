import requests
import json
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from config.settings import OLLAMA_URL, MODEL_OLLAMA


class PreguntaDefensaSchema(BaseModel):
    """
    Modelo de datos para preguntas trampa de entrevista y la estrategia de defensa del candidato.
    """
    pregunta_trampa_reclutador: str = Field(
        ...,
        description="Pregunta de entrevista técnica o conductual difícil basada explícitamente en las brechas técnicas o faltantes de seniority del candidato."
    )
    estrategia_defensa_candidato: str = Field(
        ...,
        description="Estrategia de respuesta honesta, apoyándose en proyectos reales previos para demostrar adaptabilidad y rápido aprendizaje."
    )


class KitPostulacionSchema(BaseModel):
    """
    REQUERIMIENTO 1: Modelo Pydantic v2 para el Kit de Postulación de Alta Conversión.
    """
    resumen_francotirador_negocio: str = Field(
        ...,
        description="Resumen profesional de 3-4 líneas para el CV que conecta la trayectoria real del candidato con las tecnologías requeridas y el SECTOR/INDUSTRIA del negocio (ej. Finanzas, Logística, Retail, Salud, Infraestructura)."
    )
    inmail_sniper_mensaje: str = Field(
        ...,
        description="Mensaje directo y persuasivo de máximo 120-150 palabras para LinkedIn/Correo. Estructura: 1. Qué llamó la atención del negocio de la empresa. 2. Desafío técnico clave de la oferta. 3. Logro real del CV que resuelve ese dolor. Sin clichés corporativos."
    )
    entrevista_defensa_brechas: List[PreguntaDefensaSchema] = Field(
        ...,
        description="Lista de exactamente 3 preguntas trampa de entrevista basadas en las brechas técnicas con sus respectivas respuestas tácticas."
    )


def generar_kit_postulacion(
    cv_text: str,
    job_desc: str,
    brechas_detectadas: List[str],
    empresa: str,
    cargo: str
) -> dict:
    """
    REQUERIMIENTO 2: Genera el Kit de Postulación de Alta Conversión utilizando Structured Outputs
    con Ollama y Pydantic v2.

    Args:
        cv_text: Texto consolidado del CV maestro del candidato.
        job_desc: Descripción detallada de la oferta de trabajo.
        brechas_detectadas: Lista de brechas técnicas o habilidades faltantes detectadas en la evaluación.
        empresa: Nombre de la empresa ofertante.
        cargo: Título del cargo ofertado.

    Returns:
        dict: Diccionario estructurado con resumen_francotirador_negocio, inmail_sniper_mensaje y entrevista_defensa_brechas.
    """
    json_schema = KitPostulacionSchema.model_json_schema()
    str_brechas = "\n".join([f"- {b}" for b in brechas_detectadas]) if brechas_detectadas else "Ninguna brecha crítica detectada."

    prompt = f"""
    Eres un Consultor Senior de Empleabilidad Ejecutiva y Reclutador Técnico. Tu objetivo es crear un Kit de Postulación de Alta Conversión para el candidato adaptado a la empresa {empresa} para el cargo {cargo}.

    REGLAS DE ORO STRICTAS:
    1. CERO ALUCINACIONES: Cita ÚNICAMENTE proyectos, herramientas, métricas y logros reales que existan de forma explícita en el CV DEL CANDIDATO. Prohibido inventar tecnologías no poseídas.
    2. RESUMEN FRANCOTIRADOR DE NEGOCIO: Redacta un resumen de 3-4 líneas resaltando las competencias clave del candidato y alineándolas explícitamente con el SECTOR E INDUSTRIA del negocio de {empresa} (ej. Finanzas, Logística, E-commerce, Salud, Infraestructura, SaaS).
    3. INMAIL SNIPER (MENSAJE LINKEDIN): Redacta un mensaje directo de máximo 120-150 palabras. PROHIBIDO usar relleno como "por medio de la presente" o "estimado reclutador". Usa la estructura:
       a) Qué te llamó la atención de {empresa} o su modelo de negocio.
       b) Qué desafío técnico clave pide la oferta de {cargo}.
       c) Qué logro real del CV demuestra que ya resolviste un problema similar.
    4. DEFENSA DE BRECHAS (RECRUITER MIRROR): Genera exactamente 3 preguntas trampa de entrevista basadas en estas brechas:
{str_brechas}
       Para cada pregunta, proporciona una estrategia de respuesta honesta donde el candidato reconozca la brecha pero la defienda con su experiencia arquitectónica cercana y capacidad de rápido aprendizaje.

    CV DEL CANDIDATO:
    {cv_text}

    DESCRIPCIÓN DE LA OFERTA:
    {job_desc}
    """

    payload = {
        "model": MODEL_OLLAMA,
        "prompt": prompt,
        "format": json_schema,
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }

    fallback_data = {
        "resumen_francotirador_negocio": f"Profesional enfocado en aportar valor técnico y de negocio en {empresa} como {cargo}.",
        "inmail_sniper_mensaje": f"Hola. Me llamó mucho la atención el crecimiento de {empresa} y su búsqueda para {cargo}. En mi experiencia previa he liderado proyectos similares optimizando procesos clave. Me gustaría conversar sobre cómo puedo aportar a sus desafíos actuales.",
        "entrevista_defensa_brechas": [
            {
                "pregunta_trampa_reclutador": f"Veo que la oferta pide experiencia específica en {brechas_detectadas[0] if brechas_detectadas else 'tecnologías avanzadas'}. ¿Cómo abordarías este desafío?",
                "estrategia_defensa_candidato": "Reconocer honestamente la curva de aprendizaje, apoyándote en frameworks similares que ya dominas y destacando tu velocidad de adopción previa."
            }
        ],
        "is_simulated": True,
        "model_used": "Simulación (Fallback)"
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()

        # Validar la respuesta JSON con Pydantic v2
        eval_obj = KitPostulacionSchema.model_validate_json(data["response"])
        res_dict = eval_obj.model_dump()
        res_dict["is_simulated"] = False
        res_dict["model_used"] = MODEL_OLLAMA
        return res_dict
    except Exception as e:
        print(f"Error al generar Kit de Postulación: {e}")
        return fallback_data
