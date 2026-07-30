import requests
import json
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from config.settings import OLLAMA_URL, MODEL_OLLAMA


# =====================================================================
# FLUJO 1: SANEAMIENTO Y ESTANDARIZACIÓN DEL CV BASE (PASO 2)
# =====================================================================

class ExperienciaEstandarizadaSchema(BaseModel):
    empresa: str = Field(..., description="Nombre formal de la empresa o institución.")
    cargo: str = Field(..., description="Título del cargo o posición desempeñada.")
    fechas: str = Field(..., description="Período de tiempo en la empresa (ej: '01/2021 - Presente' o '2019 - 2022').")
    vinetas_star: List[str] = Field(
        ...,
        description="Lista de logros expresados bajo la fórmula STAR: [Verbo de Acción Fuerte + Tecnología + Impacto/Resultado]."
    )


class CVBaseOptimizadoSchema(BaseModel):
    """
    REQUERIMIENTO 1: Modelo Pydantic v2 para el saneamiento inicial del CV base del candidato (Paso 2).
    """
    resumen_ejecutivo_profesional: str = Field(
        ...,
        description="Perfil general, potente y formal de 3 a 4 líneas que resume la especialidad, seniority y valor principal del candidato."
    )
    experiencias_estandarizadas: List[ExperienciaEstandarizadaSchema] = Field(
        ...,
        description="Lista de experiencias laborales estructuradas con logros STAR sin adjetivos vacíos."
    )
    skills_tecnicas: List[str] = Field(
        ...,
        description="Lista consolidada y limpia de herramientas, frameworks y tecnologías reales presentes en el CV."
    )


def optimizar_cv_base(cv_text: str) -> dict:
    """
    REQUERIMIENTO 1: FLUJO 1 - Estandariza y sanea el CV base recién cargado (Paso 2).
    Elimina lenguaje de relleno, estandariza viñetas con verbos técnicos de ingeniería
    y estructura la información sin inventar datos ni adaptar a una oferta específica.
    """
    json_schema = CVBaseOptimizadoSchema.model_json_schema()

    prompt = f"""
    Eres un Editor de Carrera Senior y Consultor de Empleabilidad. Tu tarea es sanear, estandarizar y profesionalizar el siguiente CV base.

    REGLAS DE ORO STRICTAS:
    1. VERACIDAD ABSOLUTA: PROHIBIDO inventar empresas, tecnologías, certificaciones o años de experiencia no presentes en el CV original.
    2. ELIMINACIÓN DE RELLENO: Elimina adjetivos vacíos o clichés (ej: "apasionado", "proactivo", "orientado a resultados", "motivado").
    3. FÓRMULA STAR & VERBOS DE ACCIÓN: Reescribe cada logro laboral usando verbos de ingeniería fuertes (ej: "diseñé", "implementé", "refactoricé", "migré", "automaticé", "reduje", "optimicé") combinados con la tecnología usada y el impacto logrado.
    4. SANEAMIENTO TÉCNICO: Agrupa y consolida la lista de herramientas técnicas reales.

    CV ORIGINAL:
    {cv_text}
    """

    payload = {
        "model": MODEL_OLLAMA,
        "prompt": prompt,
        "format": json_schema,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    fallback_data = {
        "resumen_ejecutivo_profesional": cv_text[:300] if cv_text else "Perfil profesional en consolidación.",
        "experiencias_estandarizadas": [],
        "skills_tecnicas": [],
        "is_simulated": True,
        "model_used": "Simulación (Fallback)"
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()

        # Validar la respuesta JSON con Pydantic v2
        eval_obj = CVBaseOptimizadoSchema.model_validate_json(data["response"])
        res_dict = eval_obj.model_dump()
        res_dict["is_simulated"] = False
        res_dict["model_used"] = MODEL_OLLAMA
        return res_dict
    except Exception as e:
        print(f"Error en optimizar_cv_base: {e}")
        return fallback_data


# =====================================================================
# FLUJO 2: SASTRERÍA QUIRÚRGICA POR OFERTA / ATS TAILORING
# =====================================================================

class ExperienciaAlineadaSchema(BaseModel):
    empresa: str = Field(..., description="Nombre de la empresa.")
    cargo: str = Field(..., description="Título del cargo adaptado con la terminología de la oferta si aplica.")
    fechas: str = Field(..., description="Fechas de la experiencia.")
    vinetas_alineadas: List[str] = Field(
        ...,
        description="Viñetas reales del candidato reformuladas usando las keywords técnicas explícitas de la oferta."
    )


class CVTailoredOfertaSchema(BaseModel):
    """
    REQUERIMIENTO 2: Modelo Pydantic v2 para la adaptación quirúrgica del CV a una oferta laboral específica.
    """
    resumen_francotirador: str = Field(
        ...,
        description="Resumen profesional de 3 líneas redactado específicamente para conectar la trayectoria real del candidato con las necesidades del Job Description."
    )
    experiencias_alineadas: List[ExperienciaAlineadaSchema] = Field(
        ...,
        description="Experiencias laborales reales reordenadas y redactadas usando el vocabulario técnico de la oferta."
    )
    skills_reordenadas_por_match: List[str] = Field(
        ...,
        description="Lista de habilidades del candidato reordenadas colocando en los primeros lugares las requeridas por la oferta."
    )


def adaptar_cv_a_oferta(cv_maestro_text: str, job_desc: str) -> dict:
    """
    REQUERIMIENTO 2: FLUJO 2 - Adapta quirúrgicamente el CV maestro del candidato a una oferta laboral específica.
    Aplica ATS Keyword Mirroring (reemplaza sinónimos por el léxico exacto del reclutador)
    y reordena las habilidades por coincidencia sin inventar datos no poseídos.
    """
    json_schema = CVTailoredOfertaSchema.model_json_schema()

    prompt = f"""
    Eres un Especialista en Optimización ATS (Applicant Tracking Systems) y Redactor Ejecutivo. Tu objetivo es adaptar el CV Maestro del candidato a la oferta de trabajo específica.

    REGLAS DE SASTRERÍA ATS (KEYWORD MIRRORING):
    1. PROHIBICIÓN DE LLM HALLUCINATIONS: NUNCA agregues tecnologías, herramientas ni años de experiencia que no estén en el CV MAESTRO.
    2. KEYWORD MIRRORING: Identifica la terminología exacta del reclutador en la oferta de trabajo y reemplaza sinónimos en el CV maestro (ej. si el CV dice "endpoints REST" y la oferta exige "API RESTful", reescríbelo como "API RESTful").
    3. RESUMEN FRANCOTIRADOR: Redacta un resumen de 3 líneas que conecte la experiencia real del candidato directamente con los requisitos clave del puesto.
    4. REORDENAMIENTO ESTRATÉGICO: Prioriza en las primeras posiciones de cada sección las competencias reales del candidato que la oferta pide explícitamente.

    CV MAESTRO DEL CANDIDATO:
    {cv_maestro_text}

    OFERTA DE TRABAJO (JOB DESCRIPTION):
    {job_desc}
    """

    payload = {
        "model": MODEL_OLLAMA,
        "prompt": prompt,
        "format": json_schema,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    fallback_data = {
        "resumen_francotirador": "Profesional con experiencia adaptada al cargo.",
        "experiencias_alineadas": [],
        "skills_reordenadas_por_match": [],
        "is_simulated": True,
        "model_used": "Simulación (Fallback)"
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()

        # Validar la respuesta JSON con Pydantic v2
        eval_obj = CVTailoredOfertaSchema.model_validate_json(data["response"])
        res_dict = eval_obj.model_dump()
        res_dict["is_simulated"] = False
        res_dict["model_used"] = MODEL_OLLAMA
        return res_dict
    except Exception as e:
        print(f"Error en adaptar_cv_a_oferta: {e}")
        return fallback_data
