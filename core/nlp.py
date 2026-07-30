import streamlit as st
from sentence_transformers import SentenceTransformer, util
from config.settings import MODEL_EMBEDDING
from config.glossary import GLOSARIO_TECNICO as GLOSARIO_FALLBACK

@st.cache_resource
def get_semantic_model():
    """
    Carga el modelo multilingüe E5 en CPU para asegurar que la VRAM (6 GB de la RTX 2060)
    se mantenga 100% reservada para la inferencia de Ollama (Llama 3.1 / Llava).
    """
    return SentenceTransformer(MODEL_EMBEDDING, device="cpu")

def generar_embedding_query(texto: str, model: SentenceTransformer):
    """
    Genera el embedding para una consulta o CV agregando el prefijo asimétrico obligatorio 'query: '.
    """
    texto_preparado = f"query: {texto}"
    return model.encode(texto_preparado, convert_to_tensor=True, device="cpu")

def generar_embedding_passage(texto: str, model: SentenceTransformer):
    """
    Genera el embedding para un pasaje o descripción de oferta agregando el prefijo asimétrico obligatorio 'passage: '.
    """
    texto_preparado = f"passage: {texto}"
    return model.encode(texto_preparado, convert_to_tensor=True, device="cpu")

def extraer_habilidades_base(cv_text, glosario_dinamico=None):
    if glosario_dinamico is None:
        glosario_dinamico = GLOSARIO_FALLBACK
        
    terminos_encontrados = []
    for tech in glosario_dinamico.keys():
        if tech.lower() in cv_text.lower():
            terminos_encontrados.append(tech)
    return terminos_encontrados

def expandir_cv_dinamico(cv_text, terminos_encontrados, glosario_dinamico=None):
    if glosario_dinamico is None:
        glosario_dinamico = GLOSARIO_FALLBACK
        
    cv_expandido = cv_text
    expansiones_dict = {}
    total_terminos = len(terminos_encontrados)
    
    for tech in terminos_encontrados:
        capas = glosario_dinamico.get(tech, {})
        
        if isinstance(capas, dict):
            # Extraer todas las palabras de las 3 capas
            sinonimos = capas.get("sinonimos", [])
            herramientas = capas.get("herramientas", [])
            impacto = capas.get("impacto", [])
            todas_expansiones = sinonimos + herramientas + impacto
            
            if todas_expansiones:
                cv_expandido += " " + " ".join(todas_expansiones)
                expansiones_dict[tech] = {
                    "Sinónimos": sinonimos,
                    "Herramientas": herramientas,
                    "Impacto": impacto
                }
                total_terminos += len(todas_expansiones)
        else:
            # Si el modelo generó una cadena de texto en vez de diccionario
            cv_expandido += f" {capas}"
            expansiones_dict[tech] = {
                "Sinónimos": [str(capas)],
                "Herramientas": [],
                "Impacto": []
            }
            total_terminos += 1
        
    return cv_expandido, expansiones_dict, total_terminos

def calcular_similitud(embedding_cv, desc_oferta, model: SentenceTransformer):
    """
    Calcula la similitud cosenoidal entre el embedding del CV (query) y la oferta (passage).
    Aplica automáticamente el prefijo 'passage: ' a la descripción de la oferta y computa en CPU.
    """
    if isinstance(desc_oferta, str):
        embedding_oferta = generar_embedding_passage(desc_oferta, model)
    else:
        embedding_oferta = desc_oferta

    similitud = util.pytorch_cos_sim(embedding_cv, embedding_oferta).item()
    return similitud

