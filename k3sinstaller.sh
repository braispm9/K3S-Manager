#!/bin/bash

# --- CONFIGURACIÓN DE TU REPOSITORIO ---
GITHUB_USER="TU_USUARIO"
REPO_NAME="TU_REPOSITORIO"
BRANCH="main"
SCRIPT_NAME="script.sh"

# URL directa para descargar el archivo raw desde GitHub
URL_RAW="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${SCRIPT_NAME}"

# Guarda el script en la carpeta actual donde ejecutas el instalador
DIRECTORIO_ACTUAL="$(cd "$(dirname "$0")" && pwd)"
DESTINO="${DIRECTORIO_ACTUAL}/${SCRIPT_NAME}"

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

# 4. Configurar el alias en ~/.bashrc apuntando a la ruta local
echo -e "\n3. Configurando el alias para el autocompletado..."
ALIAS_LINE="alias k3s='source $DESTINO'"

# Si existía un alias previo sobre k3s, lo actualizamos con la nueva ruta local
if grep -q "alias k3s=" ~/.bashrc 2>/dev/null; then
    sed -i '/alias k3s=/d' ~/.bashrc
fi

echo "" >> ~/.bashrc
echo "# Alias Consola K3s Interactiva" >> ~/.bashrc
echo "$ALIAS_LINE" >> ~/.bashrc
echo "   [OK] Alias 'k3s' actualizado en ~/.bashrc apuntando a $DESTINO."

echo -e "\n=================================================="
echo " ¡Instalación completada con éxito!"
echo " Para aplicar los cambios inmediatamente ejecuta:"
echo "   source ~/.bashrc"
echo ""
echo " Luego simplemente escribe: k3s"
echo "=================================================="
