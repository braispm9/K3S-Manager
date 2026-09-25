#!/bin/bash

# --- CONFIGURACIÓN DEL REPOSITORIO ---
GITHUB_USER="braispm9"
REPO_NAME="K3S-Manager"
BRANCH="main"
SCRIPT_NAME="k3smanager.sh"

# URL directa para descargar el archivo raw desde GitHub
URL_RAW="https://raw.githubusercontent.com/braispm9/K3S-Manager/refs/heads/main/k3smanager.sh"

# Guardado el script en la carpeta actual donde se ejecuta el instalador
DIRECTORIO_ACTUAL="$(cd "$(dirname "$0")" && pwd)"
DESTINO="${DIRECTORIO_ACTUAL}/${SCRIPT_NAME}"

echo "====================================="
echo " Instalador de K3s Manager (Bash/Zsh)"
echo "====================================="

# 1. Detectar el usuario real (si se ejecuta con sudo) y su directorio HOME
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(eval echo "~$SUDO_USER")
else
    REAL_USER="$(whoami)"
    REAL_HOME="$HOME"
fi

echo "Instalando para el usuario: $REAL_USER ($REAL_HOME)"

# 2. Comprobar e instalar dependencias básicas del sistema
echo -e "\n1. Verificando dependencias del sistema..."

DEPENDENCIAS=("curl" "kubectl" "fzf")

for dep in "${DEPENDENCIAS[@]}"; do
    if ! command -v "$dep" &> /dev/null; then
        echo "   [!] '$dep' no está instalado. Intentando instalar..."
        if command -v apt &> /dev/null; then
            apt update && apt install -y "$dep"
        elif command -v yum &> /dev/null; then
            yum install -y "$dep"
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

# 3. Descargar el script principal desde GitHub
echo -e "\n2. Descargando el script desde GitHub..."
wget --header="Authorization: token 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" \ https:raw.githubusercontent.com/braispm9/K3S-Manager/main/k3smanager.sh

if [ $? -eq 0 ] && [ -s "$DESTINO" ]; then
    echo "   [OK] Script descargado correctamente en: $DESTINO"
else
    echo "   [X] Error al descargar el script desde GitHub. Revisa la URL y la configuración del repositorio."
    rm -f "$DESTINO"
    exit 1
fi

# Ajustar permisos del script descargado para el usuario real
chmod +x "$DESTINO"
chown "$REAL_USER" "$DESTINO" 2>/dev/null

# 4. Detectar el archivo de configuración (.zshrc o .bashrc) del usuario real
echo -e "\n3. Configurando el alias..."

# Obtener la shell configurada para el usuario real
USER_SHELL=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f7)

if [[ "$USER_SHELL" =~ "zsh" ]] || [ -f "$REAL_HOME/.zshrc" ]; then
    RC_FILE="$REAL_HOME/.zshrc"
else
    RC_FILE="$REAL_HOME/.bashrc"
fi

ALIAS_LINE="alias k3smanager='source $DESTINO'"

# Si el archivo no existe, lo crea
touch "$RC_FILE"

# Si existía un alias previo sobre k3smanager en el archivo detectado, lo limpiamos
if grep -q "alias k3smanager=" "$RC_FILE" 2>/dev/null; then
    sed -i.bak '/alias k3smanager=/d' "$RC_FILE" 2>/dev/null || sed -i '' '/alias k3smanager=/d' "$RC_FILE" 2>/dev/null
fi

echo "" >> "$RC_FILE"
echo "# Alias K3s Manager" >> "$RC_FILE"
echo "$ALIAS_LINE" >> "$RC_FILE"

# Ajustar propietarios del archivo de configuración editado
chown "$REAL_USER" "$RC_FILE" 2>/dev/null

echo "   [OK] Alias 'k3smanager' configurado en $RC_FILE"

echo -e "\n=================================================="
echo " ¡Instalación completada con éxito!"
echo " Para aplicar los cambios inmediatamente ejecuta en tu consola de usuario:"
echo "   source $RC_FILE"
echo ""
echo " Luego simplemente escribe: k3smanager"
echo "=================================================="
