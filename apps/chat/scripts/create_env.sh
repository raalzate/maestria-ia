#!/bin/bash

echo ">>> Creando ambiente virtual..."
python3 -m venv chat-env

echo ">>> Activando ambiente..."
source chat-env/bin/activate

echo ">>> Actualizando pip..."
pip install --upgrade pip

echo ">>> Instalando dependencias..."
pip install -r requirements.txt

echo ">>> Instalación completa."
echo ">>> Para activar el ambiente nuevamente:"
echo "source chat-env/bin/activate"
