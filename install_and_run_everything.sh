#!/bin/bash
echo "======================================================="
echo "INSTALADOR COMPLETO: IA LOCAL + INTERFAZ DEL AGENTE"
echo "======================================================="
echo ""

echo "1/6 - Instalando dependencias de sistema (Ollama, Python venv y TeX Live para PDF)..."
# Instalar Ollama si no existe
if ! command -v ollama &> /dev/null
then
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Instalar dependencias de Ubuntu
sudo apt update
sudo apt install -y python3-venv python3-pip texlive-latex-base texlive-latex-extra texlive-fonts-recommended

echo ""
echo "2/6 - Descargando modelos de IA (Llama3.1 y Llava)..."
# En Ubuntu, la instalación de Ollama crea un servicio systemd automático
# que ya está corriendo en el fondo.
ollama pull llama3.1
ollama pull llava

echo ""
echo "3/6 - Configurando el entorno virtual de Python..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "4/6 - Instalando navegadores para web scraping (Playwright)..."
playwright install chromium
playwright install-deps

echo ""
echo "5/6 - El Servidor de IA (Ollama) ya corre como servicio de sistema en Ubuntu."

echo ""
echo "6/6 - Levantando la aplicacion web de Streamlit..."
chmod +x run.sh
./run.sh
