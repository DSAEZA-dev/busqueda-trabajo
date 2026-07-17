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
4. **Mejora del CV:** Cuenta con un módulo de evaluación por LLM capaz de analizar tu perfil actual, corregir la redacción y potenciar tus logros.
5. **Historial y Seguimiento:** Almacena tu historial de ofertas evaluadas para que lleves un control claro de a dónde deberías postular.

## 🛠️ Tecnologías Utilizadas

- **Frontend / UI:** [Streamlit](https://streamlit.io/)
- **Scraping:** [Playwright](https://playwright.dev/) (Asíncrono)
- **Base de Datos:** SQLite
- **Inteligencia Artificial Local:** [Ollama](https://ollama.ai/) (Modelo: `llama3.1`)
- **Procesamiento NLP:** `sentence-transformers`
- **Lenguaje Base:** Python 3.x

## 🚀 Cómo instalar y ejecutar (Windows)

El proyecto incluye un instalador automático que configurará todo por ti (descarga de IA local, dependencias, etc.).

1. Clona este repositorio en tu computadora.
2. Haz doble clic en el archivo `install_and_run_everything.bat`.

Este script se encargará de:
- Instalar **Ollama** vía `winget`.
- Descargar el modelo **Llama 3.1** (aprox. 4.7 GB).
- Iniciar el servidor de IA en segundo plano.
- Levantar la aplicación web de Streamlit.

*(Nota: En ejecuciones futuras, solo necesitas correr el archivo `run.bat` si ya instalaste todo previamente).*

## 📂 Estructura Principal del Proyecto

```text
├── app.py                      # Archivo principal (UI de Streamlit)
├── install_and_run_everything.bat # Instalador automático
├── run.bat                     # Ejecutador normal del proyecto
├── requirements.txt            # Dependencias de Python
├── config/                     # Configuraciones geográficas y generales
├── core/                       # Lógica principal
│   ├── llm_evaluator.py        # Interacción con Ollama (Llama 3.1)
│   ├── nlp.py                  # Modelos de similitud semántica
│   └── scraper.py              # Motor de scraping (Playwright)
├── database/                   # Manejo de SQLite (historial y perfiles)
└── ui/                         # Componentes visuales y CSS personalizado
```

## 🤝 Contribuciones

Este proyecto es de código abierto. ¡Las sugerencias, *issues* y *pull requests* son más que bienvenidos para seguir mejorando el Agente!
