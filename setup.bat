@echo off
echo Creando entorno virtual...
python -m venv .venv
call .venv\Scripts\activate.bat
echo Instalando dependencias...
pip install -r requirements.txt
playwright install
echo Instalacion completada!
echo Para correr la app usa: run.bat
