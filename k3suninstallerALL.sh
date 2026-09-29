#!/bin/bash

# --- CONFIGURACIÓN DEL REPOSITORIO ---
GITHUB_USER="braispm9"
REPO_NAME="K3S-Manager"
BRANCH="main"

# Variables necesarias
INSTALL_DIR="/usr/local/bin"
DESTINO_UNINSTALLER="${INSTALL_DIR}/k3suninstaller.sh"
UNINS_NAME="k3suninstaller.sh"

RAW_URL_UNINS="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${UNINS_NAME}"

# --- VERIFICACIÓN DE PERMISOS ---
if [ "$EUID" -ne 0 ]; then
    echo -e "\n\033[1;31m[X] Error: Este desinstalador necesita permisos de administrador.\033[0m"
    echo "    Por favor, ejecútalo escribiendo:"
    echo -e "    \033[1;33msudo ./k3suninstallerALL.sh\033[0m\n"
    exit 1
fi

# --- IDENTIFICAR AL USUARIO REAL ---
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(eval echo "~$SUDO_USER")
else
    REAL_USER="$(whoami)"
    REAL_HOME="$HOME"
fi

echo "Descargando desinstalador desde GitHub..."

# --- DESCARGA DEL ARCHIVO ---
curl -fsSL -o "$DESTINO_UNINSTALLER" "$RAW_URL_UNINS"

# --- PERMISOS DE EJECUCIÓN ---
chmod +x "$DESTINO_UNINSTALLER"

echo ""
echo "=================================================="
echo " Limpiando acceso desde shell..."
echo "=================================================="

# --- FUNCIÓN PARA LIMPIAR SOURCE ---
limpiar_source() {
    local RC_FILE="$1"
    local USER_NAME="$2"
    
    if [ ! -f "$RC_FILE" ]; then
        return
    fi
    
    # Limpiar líneas de source/alias relacionadas con k3sinstaller y k3smanager
    sed -i.bak '/source.*k3sinstaller.sh/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/\. .*k3sinstaller.sh/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/alias k3smanager=/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/alias k3smanager-gui=/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/export KUBECONFIG/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/# --- K3s Manager Shortcuts & Environment ---/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/# --- K3s Installer Source ---/d' "$RC_FILE" 2>/dev/null
    
    chown "$USER_NAME":"$USER_NAME" "$RC_FILE" 2>/dev/null
    echo "    • Limpiado: $RC_FILE"
}

# --- DETECTAR SHELL DEL USUARIO Y LIMPIAR ---
USER_SHELL=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f7)

if [[ "$USER_SHELL" =~ "zsh" ]] || [ -f "$REAL_HOME/.zshrc" ]; then
    limpiar_source "$REAL_HOME/.zshrc" "$REAL_USER"
fi

if [ -f "$REAL_HOME/.bashrc" ]; then
    limpiar_source "$REAL_HOME/.bashrc" "$REAL_USER"
fi

echo "    • Configuración limpiada"
echo ""

# --- EJECUTAR EL DESINSTALADOR ---
echo "=================================================="
echo " Ejecutando desinstalador de K3s Manager..."
echo "=================================================="
echo ""

sudo -u "$REAL_USER" "$DESTINO_UNINSTALLER"
