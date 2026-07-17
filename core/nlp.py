import streamlit as st
from sentence_transformers import SentenceTransformer, util
from config.settings import MODEL_EMBEDDING
from config.glossary import GLOSARIO_TECNICO as GLOSARIO_FALLBACK

@st.cache_resource
def get_semantic_model():
    return SentenceTransformer(MODEL_EMBEDDING)

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
        
    return cv_expandido, expansiones_dict, total_terminos

def calcular_similitud(embedding_cv, desc_oferta, model):
    embedding_oferta = model.encode(desc_oferta, convert_to_tensor=True)
    similitud = util.pytorch_cos_sim(embedding_cv, embedding_oferta).item()
    return similitud
