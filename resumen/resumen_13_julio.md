# Resumen de Sesión - Proyecto Búsqueda de Empleo con IA
**Fecha:** 13 de Julio de 2026

## 1. Reparación de Extracción de Datos (Scraping)
- **Computrabajo:** Se actualizaron los selectores CSS y HTML (nombres de clases dinámicos) que estaban provocando que las ofertas retornaran vacías. El scraper fue estabilizado y ahora extrae correctamente Títulos, Empresas y URLs.
- **Ubicación:** Se mejoró la lógica de extracción de ubicación geográfica para tolerar inconsistencias en el portal.

## 2. Optimización de Búsqueda de Cargos
- **Agrupación Bilingüe:** Se modificó el prompt de Llama 3.1 para que cuando sugiera cargos que son equivalentes (ej. *Data Analyst* y *Analista de Datos*), los agrupe en la UI (ej. `Data Analyst / Analista de Datos`).
- **Multiscraping Invisible:** Se adaptó el algoritmo en `app.py` para que detecte estos conceptos agrupados y lance múltiples búsquedas paralelas (una por idioma) sin saturar las 3 opciones máximas del usuario.

## 3. Glosario Técnico y Expansión Semántica (La Mejora Estrella)
- **Migración a 3 Capas:** Se abandonó la lista plana de conceptos técnicos para pasar a una arquitectura de 3 capas por habilidad: **Sinónimos, Herramientas e Impacto/Negocio**.
- **Generación Dinámica con LLM:** Se eliminó el uso de un diccionario estático preconfigurado. Ahora, Llama 3.1 lee el CV y **crea un diccionario de expansión personalizado al vuelo** (Glosario Dinámico).
- **Interfaz de Usuario (UI):** Se agregó un panel desplegable en la Fase 3 de la aplicación para que el candidato pueda visualizar exactamente qué conceptos y capas semánticas detectó la IA de su CV.
- **Prevención de Alucinaciones:** Se refinó agresivamente el prompt para evitar que Llama 3.1 "copiara" los ejemplos técnicos del prompt y se forzó a que extraiga habilidades no convencionales, tales como herramientas de negocio (Power BI, Excel) y metodologías (Scrum, Estandarización).

## 4. Mejoras en Experiencia y Filtros
- **Columna "Modalidad":** Se implementó la extracción de modalidad (Presencial, Remoto, Híbrido) directamente desde Computrabajo y se integró como una columna visual nueva en las tablas finales de Pandas.
- **Expansión a Nuevos Portales:** Se agregaron los motores de búsqueda (scrapers) para **Laborum** y **Trabajando.com** dentro de la tubería de multiscraping con Playwright. (Con la advertencia técnica de que estos sitios poseen defensas anti-bots avanzadas como Cloudflare y Datadome, lo cual limitará la extracción comparado con Computrabajo).

---
*Fin del resumen.*
