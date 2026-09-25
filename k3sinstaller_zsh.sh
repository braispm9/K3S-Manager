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
echo " Instalador Automático de K3s Manager (Bash/Zsh)"
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
        elif command -v brew &> /dev/null; then
            brew install "$dep"
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

# 4. Detectar el archivo de configuración de la Shell (Zsh o Bash)
echo -e "\n3. Configurando el alias..."

IF_ZSH=$(echo "$SHELL" | grep -i "zsh")

if [ -n "$IF_ZSH" ] || [ -f "$HOME/.zshrc" ]; then
    RC_FILE="$HOME/.zshrc"
else
    RC_FILE="$HOME/.bashrc"
fi

ALIAS_LINE="alias k3smanager='source $DESTINO'"

# Si existía un alias previo sobre k3smanager en el archivo detectado, lo limpiamos
if grep -q "alias k3smanager=" "$RC_FILE" 2>/dev/null; then
    sed -i.bak '/alias k3smanager=/d' "$RC_FILE" 2>/dev/null || sed -i '' '/alias k3smanager=/d' "$RC_FILE" 2>/dev/null
fi

echo "" >> "$RC_FILE"
echo "# Alias K3s Manager" >> "$RC_FILE"
echo "$ALIAS_LINE" >> "$RC_FILE"
echo "   [OK] Alias 'k3smanager' configurado en $RC_FILE"

echo -e "\n=================================================="
echo " ¡Instalación completada con éxito!"
echo " Para aplicar los cambios inmediatamente ejecuta:"
echo "   source $RC_FILE"
echo ""
echo " Luego simplemente escribe: k3smanager"
echo "=================================================="
