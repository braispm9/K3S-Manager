#!/bin/bash

# --- CONFIGURACIÓN DE TU REPOSITORIO ---
GITHUB_USER="braispm9"
REPO_NAME="K3S-Manager"
BRANCH="main"
SCRIPT_NAME="k3smanager.sh"

# URL directa para descargar el archivo raw desde GitHub
URL_RAW="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${SCRIPT_NAME}"
DESTINO="$HOME/.k3s_console.sh"

echo "=================================================="
echo " Instalador Automático de la Consola K3s"
echo "=================================================="

# 1. Comprobar e instalar dependencias básicas del sistema
echo -e "\n1. Verificando dependencias del sistema..."

DEPENDENCIAS=("curl" "kubectl")

for dep in "${DEPENDENCIAS[@]}"; do
    if ! command -v "$dep" &> /dev/null; then
        echo "   [!] '$dep' no está instalado. Intentando instalar..."
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y "$dep"
        elif command -v yum &> /dev/null; then
            sudo yum install -y "$dep"
        else
            echo "   [X] No se pudo instalar '$dep' automáticamente. Por favor instálalo manualmente."
            exit 1
        fi
    else
        echo "   [OK] '$dep' ya está instalado."
    fi
done

# 2. Descargar el script principal desde GitHub
echo -e "\n2. Descargando el script desde GitHub..."
curl -sSL "$URL_RAW" -o "$DESTINO"

if [ $? -eq 0 ] && [ -s "$DESTINO" ]; then
    echo "   [OK] Script descargado correctamente en: $DESTINO"
else
    echo "   [X] Error al descargar el script desde GitHub. Revisa la URL y la configuración del repositorio."
    rm -f "$DESTINO"
    exit 1
fi

# 3. Asignar permisos de ejecución
chmod +x "$DESTINO"

# 4. Configurar el alias en ~/.bashrc para soportar autocompletado nativo
echo -e "\n3. Configurando el alias para el autocompletado..."
ALIAS_LINE="alias k3s='source $DESTINO'"

if grep -qF "$ALIAS_LINE" ~/.bashrc 2>/dev/null; then
    echo "   [OK] El alias 'k3s' ya está en ~/.bashrc."
else
    echo "" >> ~/.bashrc
    echo "# Alias Consola K3s Interactiva" >> ~/.bashrc
    echo "$ALIAS_LINE" >> ~/.bashrc
    echo "   [OK] Alias 'k3s' añadido a ~/.bashrc."
fi

echo -e "\n=================================================="
echo " ¡Instalación completada con éxito!"
echo " Para aplicar los cambios inmediatamente ejecuta:"
echo "   source ~/.bashrc"
echo ""
echo " Luego simplemente escribe: k3s"
echo "=================================================="
