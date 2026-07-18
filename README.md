# 🤖 Agente Buscador de Empleo Inteligente

¡Bienvenido al **Agente Buscador de Empleo Inteligente**! 
Este proyecto es una aplicación de inteligencia artificial diseñada para automatizar, optimizar y personalizar la búsqueda de empleo. A través del uso de modelos de lenguaje locales (LLMs) y técnicas de procesamiento de lenguaje natural (NLP), la herramienta es capaz de analizar tu currículum, buscar ofertas laborales relevantes en internet y evaluar qué tan compatibles son con tu perfil.

## 🎯 Objetivos del Proyecto

- **Automatización de Búsqueda:** Eliminar el proceso manual y repetitivo de buscar ofertas en distintos portales de empleo.
- **Match Inteligente (Similitud Semántica):** Comparar directamente las habilidades del candidato con los requerimientos del cargo utilizando modelos de NLP (`sentence-transformers`).
- **Análisis de Perfil Avanzado:** Evaluar de forma exhaustiva el CV del usuario y generar recomendaciones de mejora, pudiendo reconstruir el CV para que sea más atractivo.
- **Privacidad y Control (Local AI):** Ejecutar la inteligencia artificial de manera local usando **Ollama (Llama 3.1)**, garantizando que los datos personales (RUT, CV, información de contacto) no sean enviados a servidores externos de terceros.

## 🤔 ¿Por qué se hace este proyecto?

La búsqueda de empleo moderna puede ser un proceso frustrante, lento y muchas veces desmotivador. Los profesionales invierten horas leyendo ofertas que no se adaptan a su nivel de experiencia, salario esperado o modalidad de trabajo. 

Además, adaptar el currículum a cada oferta toma tiempo valioso. Este proyecto nace de la necesidad de **empoderar al candidato**, dándole una herramienta tecnológica avanzada que actúe como su propio "cazatalentos personal".

## 💡 ¿En qué te puede ayudar?

1. **Ahorro de Tiempo:** El bot realiza _multiscraping_ en portales (como Computrabajo, entre otros) extrayendo las ofertas y centralizándolas en una interfaz limpia.
2. **Filtrado Real:** Descarta automáticamente las ofertas que no alcanzan un umbral mínimo de similitud con tu perfil, ahorrándote el leer ofertas irrelevantes.
3. **Análisis de Brechas (Gap Analysis):** La IA evalúa la oferta y te dice exactamente qué habilidades tienes, cuáles te faltan y por qué eres (o no) un buen candidato.
4. **Mejora y Generación de CVs:** Cuenta con un módulo de evaluación por LLM capaz de analizar tu perfil, corregir la redacción y exportar tu CV a un archivo `.tex` o `.pdf` con formato profesional. También soporta generar código LaTeX a partir de imágenes de referencia.
5. **Historial y Seguimiento:** Almacena tu historial de ofertas evaluadas para que lleves un control claro de a dónde deberías postular.

---

## 🔄 ¿Cómo funciona la app? (Fases paso a paso)

La aplicación guía al usuario a través de **7 pasos organizados en 4 fases**, desde la identificación hasta la postulación final. A continuación se detalla cada una:

### 🪪 Fase 1: Identidad y Ubicación

**¿Qué se hace aquí?**
Se ingresa el **RUT** del usuario. Este actúa como identificador único para guardar y recuperar perfiles, CVs y configuraciones entre sesiones.

**Características:**
- Si el RUT ya existe en la base de datos, el sistema **carga automáticamente** toda la información previa (CV, región, datos del perfil analizado, CV estructurado).
- Se puede especificar opcionalmente la **región y comuna** de residencia, lo cual se usa más adelante para filtrar ofertas geográficamente y detectar ofertas "cerca de tu casa".

---

### 📄 Fase 2: Radiografía del Perfil

Esta es la fase más rica de la aplicación. Aquí el usuario construye o sube su CV para que la IA pueda entenderlo. Tiene **dos opciones** (tabs) que pueden combinarse:

#### Opción A: Subir Archivo
- Soporta archivos **`.txt`**, **`.md`** y **`.pdf`**.
- **PDFs digitales** (generados desde Word, Google Docs, Canva): el texto se extrae instantáneamente con `PyMuPDF`.
- **PDFs escaneados** (imágenes): si el texto extraído tiene menos de 100 caracteres, el sistema activa automáticamente **EasyOCR** (reconocimiento óptico de caracteres) para "leer" el documento como haría un humano. Soporta español e inglés.

#### Opción B: Constructor de CV con IA
Un formulario interactivo donde puedes llenar manualmente tu información profesional:
- **Datos personales:** Nombre completo, título profesional.
- **Resumen profesional:** Con botón `✨ Mejorar con IA` que reescribe el texto para hacerlo más impactante.
- **Experiencias laborales:** Múltiples experiencias con cargo, empresa, fechas, logros y aprendizajes. Cada campo tiene su propio botón de mejora con IA.
- **Formación y cursos:** Cursos, certificaciones y títulos con institución y fechas.
- **Habilidades técnicas y blandas:** Listado libre con mejora por IA.

**🤖 Autocompletar desde el CV subido:** Si subiste un archivo en la Opción A (incluso un PDF), puedes hacer clic en este botón en la Opción B. La IA (Ollama / Llama 3.1) parsea todo el texto extraído y rellena automáticamente los campos del formulario (nombre, experiencias, habilidades, etc.).

**Acciones disponibles en esta fase:**
| Botón | Función |
|---|---|
| 💾 **Consolidar mi CV** | Convierte todos los campos del formulario en un texto plano estructurado que la IA puede procesar. |
| 🪄 **Mejorar TODO con IA** | La IA reescribe completamente el CV consolidado para hacerlo más profesional e impactante. |
| 💾 **Guardar CV al Perfil** | Persiste todo (CV + datos estructurados) en la base de datos vinculado al RUT, para recuperarlo en futuras sesiones. |

**📄 Exportación LaTeX:**
- Puedes generar un archivo `.tex` con formato ATS-friendly directamente desde esta fase.
- También puedes subir una **imagen de referencia** de un diseño de CV que te guste, y la IA de visión (**Llava**) generará código LaTeX que imite ese diseño con tus datos.

---

### 🧠 Fase 3: Sugerencias Inteligentes de Cargo

**¿Qué se hace aquí?**
La IA analiza profundamente el CV y genera:

1. **Profesión detectada:** Identifica automáticamente tu perfil profesional.
2. **Top 10 cargos afines:** Una tabla con los cargos más compatibles con tu perfil, ordenados por % de afinidad. Se muestra con barras visuales de progreso.
3. **Glosario Técnico Dinámico:** La IA detecta tus habilidades clave y genera 3 capas de expansión semántica por cada una:
   - *Sinónimos:* Otras formas de nombrar la misma tecnología.
   - *Herramientas:* Software y frameworks relacionados.
   - *Impacto:* Verbos y resultados de negocio asociados.
   
   > Este glosario se usa después para "expandir" tu CV antes de compararlo con las ofertas, mejorando dramáticamente la precisión del match semántico.

4. **Generador LaTeX ATS-friendly:** Desde aquí también puedes exportar un CV optimizado para pasar filtros automáticos de reclutamiento (ATS).

---

### 🎯 Fase 4: Decisión y Cacería

**¿Qué se hace aquí?**
Seleccionas hasta **3 cargos** de los sugeridos por la IA (o escribes uno manual) y configuras los filtros de búsqueda.

**Filtros disponibles:**
- **Modalidad:** Presencial, Híbrido, Remoto o Indiferente.
- **Región y comuna:** Filtra geográficamente usando la base de datos de regiones y comunas de Chile.

Al hacer clic en **🚀 Comenzar Búsqueda Multicargo**, se ejecutan los siguientes pasos automáticamente:

#### Paso 4: La Cacería Multicargo
- Se despliegan bots de scraping asíncronos (con **Playwright**) que recorren portales de empleo buscando cada cargo seleccionado.
- Se filtran ofertas por ubicación geográfica y se eliminan duplicados.

#### Paso 5: El Embudo Matemático (El Colador)
- Se calcula la **similitud cosenoidal** entre el CV expandido (con el glosario técnico) y la descripción de cada oferta usando `sentence-transformers`.
- Las ofertas que no superan el umbral de similitud configurado (por defecto **70%**) se descartan automáticamente.
- Se muestran métricas: ofertas totales extraídas, descartadas y candidatas.

#### Paso 6: El Juez Implacable (Auditoría con IA Local)
- Cada oferta candidata pasa por una **evaluación profunda con Llama 3.1** que analiza:
  - ✅ **Pros:** Por qué tu perfil hace match.
  - ⚠️ **Brechas:** Qué habilidades o experiencia te faltan.
  - 💡 **Consejo táctico:** Recomendaciones específicas para postular.
  - 📍 **Proximidad:** Detecta si la oferta está cerca de tu casa.
  - 🏆 **Puntaje (1-10):** Calificación general de compatibilidad.
- Se puede **interrumpir** el análisis en cualquier momento si hay demasiadas ofertas.

#### Paso 7: El Tablero de Comando Final
- Se muestran solo las ofertas con puntaje **≥ 7.5/10**, ordenadas de mejor a peor.
- Por cada oferta puedes:
  - 🔗 **Ir a la postulación** directamente.
  - 👍/👎 Dar **feedback** sobre la relevancia.
  - 💾 **Guardar** la oferta en la base de datos vinculada a tu RUT.
  - 🤖 **Generar un CV LaTeX personalizado** optimizado para esa oferta específica.
  - 📄 **Exportar a PDF** compilando localmente con MiKTeX/pdflatex.

---

### 📚 Historial Guardado

Una pestaña separada donde puedes consultar todas las ofertas que has guardado previamente, buscando por RUT.

---

## 🚀 ¿Cómo potenciar la herramienta?

### Para usuarios
- **Sube tu CV en PDF** y deja que la IA lo autocomplete — luego usa los botones de "Mejorar con IA" en cada campo para potenciar cada sección individualmente.
- **Usa el glosario técnico** como guía de aprendizaje: te muestra exactamente qué tecnologías y herramientas deberías aprender para ampliar tu perfil.
- **Genera CVs personalizados por oferta** en el Paso 7 — cada empresa recibe un CV optimizado para lo que piden.
- **Sube una imagen de referencia** de un CV bonito que veas en internet, y la IA replicará ese diseño con tus datos.

### Para desarrolladores
- **Agregar más portales de scraping:** Editar `core/scraper.py` para incluir nuevos motores (LinkedIn, Indeed, etc.).
- **Cambiar el modelo de IA:** En `config/settings.py`, cambiar `MODEL_OLLAMA` a cualquier modelo compatible con Ollama (ej. `mistral`, `codellama`, `gemma2`).
- **Ajustar el umbral de similitud:** Modificar `SIMILARITY_THRESHOLD` en `config/settings.py` (por defecto 0.70). Subirlo descarta más ofertas; bajarlo es más permisivo.
- **Mejorar el OCR:** En `core/pdf_extractor.py`, puedes ajustar el `ocr_threshold` (actualmente 100 caracteres) o cambiar los idiomas del lector EasyOCR.
- **Agregar nuevos idiomas:** EasyOCR soporta +80 idiomas. Solo agrega el código del idioma en `get_ocr_reader()`.

---

## 🛠️ Tecnologías Utilizadas (100% Gratuitas y Open Source)

El proyecto fue diseñado bajo una premisa fundamental: **democratizar el acceso a la IA para la búsqueda de empleo sin costos ocultos ni suscripciones a APIs de terceros.** Todas las tecnologías elegidas son completamente gratuitas, open source y se ejecutan localmente para garantizar la máxima privacidad de tus datos.

| Categoría | Tecnología | ¿Por qué la elegimos? |
|---|---|---|
| **Frontend / UI** | [Streamlit](https://streamlit.io/) | Permite crear interfaces web interactivas y hermosas usando solo Python. Es ideal para aplicaciones de IA orientadas a datos. |
| **Scraping y APIs** | [Playwright](https://playwright.dev/) + `playwright-stealth` + `aiohttp` | `Playwright` extrae portales dinámicos. `playwright-stealth` evade bloqueos antibots avanzados (Cloudflare/Datadome). `aiohttp` se usa para consumir APIs directamente (ej. GetOnBoard) a máxima velocidad sin usar el navegador. |
| **Base de Datos** | SQLite | Incluida por defecto en Python. No requiere instalación ni configuración de servidores externos, siendo perfecta para uso personal local. |
| **IA Local (LLM)** | [Ollama](https://ollama.ai/) (Modelos: `llama3.1`, `llava`) | Permite ejecutar modelos de lenguaje masivos **en tu propia máquina**. Es 100% gratuito (adiós a las facturas de OpenAI) y tu currículum nunca sale de tu computador. |
| **Procesamiento NLP** | `sentence-transformers` (`paraphrase-MiniLM-L6-v2`) | Modelo de embeddings ligero y súper rápido. Calcula la compatibilidad matemática (Match) entre el CV y las ofertas sin necesidad de una tarjeta gráfica de alta gama. |
| **Extracción de PDF** | `PyMuPDF` + `EasyOCR` | `PyMuPDF` es ultrarrápido para extraer texto digital de un PDF. `EasyOCR` se agregó como "Plan B" para leer imágenes o PDFs escaneados gratuitamente sin pagar costosas APIs de visión (Google/AWS). |
| **Generación PDF** | `pdflatex` (vía [MiKTeX](https://miktex.org/)) | El estándar absoluto mundial para generar documentos (LaTeX). Permite crear PDFs de altísima calidad profesional y 100% legibles por los sistemas ATS (robots de reclutamiento). |
| **Lenguaje Base** | Python 3.x | El lenguaje líder y estándar en el ecosistema mundial de Inteligencia Artificial, web scraping y automatización. |

## 🚀 Cómo instalar y ejecutar (Windows)

El proyecto incluye un instalador automático que configurará todo por ti (descarga de IA local, dependencias, etc.).

1. Clona este repositorio en tu computadora.
2. Haz doble clic en el archivo `install_and_run_everything.bat`.

Este script de instalación completo se encargará de:
- Instalar **Ollama** y **MiKTeX** (para exportar PDF local) vía `winget`.
- Descargar los modelos **Llama 3.1** y **Llava** (para análisis multimodal de imágenes).
- Crear un entorno virtual (`.venv`), instalar las dependencias de Python y los navegadores de `playwright`.
- Iniciar el servidor de IA en segundo plano.
- Levantar la aplicación web de Streamlit.

*(Nota: En ejecuciones futuras, solo necesitas correr el archivo `run.bat` si ya instalaste todo previamente).*

## 🐧 Cómo instalar y ejecutar (Ubuntu / Linux)

El proceso en Ubuntu es igual de automático. Solo debes asegurarte de tener permisos de ejecución en los scripts.

1. Clona este repositorio en tu computadora.
2. Abre la terminal en la carpeta del proyecto y dale permisos al instalador:
   ```bash
   chmod +x install_and_run_everything.sh
   ```
3. Ejecútalo:
   ```bash
   ./install_and_run_everything.sh
   ```

Este script hará un proceso análogo al de Windows, instalando Ollama mediante `curl`, configurando `texlive` por APT para el soporte PDF, descargando los modelos, instalando Playwright y finalmente arrancando Streamlit.

*(Nota: En ejecuciones futuras, solo necesitas correr el archivo `./run.sh`)*

## 📂 Estructura Principal del Proyecto

```text
├── app.py                        # Archivo principal (UI de Streamlit, todas las fases)
├── install_and_run_everything.bat # Instalador automático (Windows)
├── install_and_run_everything.sh  # Instalador automático (Linux)
├── run.bat                       # Ejecutador normal del proyecto (Windows)
├── run.sh                        # Ejecutador normal del proyecto (Linux)
├── requirements.txt              # Dependencias de Python
├── config/
│   ├── settings.py               # Configuración de modelos, umbrales y rutas
│   ├── geography.py              # Base de datos de regiones y comunas de Chile
│   └── glossary.py               # Glosario técnico de fallback
├── core/
│   ├── llm_evaluator.py          # Interacción con Ollama (Llama 3.1 / Llava)
│   ├── nlp.py                    # Modelos de similitud semántica y expansión de CV
│   ├── pdf_extractor.py          # Extracción de texto de PDF (directo + OCR con EasyOCR)
│   └── scraper.py                # Motor de multiscraping asíncrono (Playwright)
├── database/
│   └── db_manager.py             # Manejo de SQLite (historial, perfiles y CVs)
└── ui/
    └── components.py             # Componentes visuales, CSS personalizado y tablas
```

## 🤝 Contribuciones

Este proyecto es de código abierto. ¡Las sugerencias, *issues* y *pull requests* son más que bienvenidos para seguir mejorando el Agente!
