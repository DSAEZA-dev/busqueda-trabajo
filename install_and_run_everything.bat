@echo off
echo =======================================================
echo INSTALADOR COMPLETO: IA LOCAL + INTERFAZ DEL AGENTE
echo =======================================================
echo.
echo 1/4 - Instalando Ollama (El Motor de Inteligencia Artificial Local)...
winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements --silent

echo.
echo 2/4 - Descargando el modelo llama3.1 (Esto tomara varios minutos, son aproximadamente 4.7 GB)...
set OLLAMA_EXE="%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
%OLLAMA_EXE% pull llama3.1

echo.
echo 3/4 - Iniciando el Servidor de IA en segundo plano...
start /min cmd /c "%OLLAMA_EXE% run llama3.1"

echo.
echo 4/4 - Levantando la aplicacion web de Streamlit...
call run.bat
