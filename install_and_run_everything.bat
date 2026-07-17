@echo off
echo =======================================================
echo INSTALADOR COMPLETO: IA LOCAL + INTERFAZ DEL AGENTE
echo =======================================================
echo.
echo 1/6 - Instalando dependencias de sistema (Ollama y MiKTeX)...
winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements --silent
winget install MiKTeX.MiKTeX --accept-source-agreements --accept-package-agreements --silent

echo.
echo 2/6 - Descargando modelos de IA (Llama3.1 y Llava)...
set OLLAMA_EXE="%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
%OLLAMA_EXE% pull llama3.1
%OLLAMA_EXE% pull llava

echo.
echo 3/6 - Configurando el entorno virtual de Python...
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo 4/6 - Instalando navegadores para web scraping (Playwright)...
playwright install chromium

echo.
echo 5/6 - Iniciando el Servidor de IA en segundo plano...
start /min cmd /c "%OLLAMA_EXE% run llama3.1"

echo.
echo 6/6 - Levantando la aplicacion web de Streamlit...
call run.bat

