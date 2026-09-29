#!/bin/bash

# --- CONFIGURACIÓN DEL REPOSITORIO ---
GITHUB_USER="braispm9"
REPO_NAME="K3S-Manager"
BRANCH="main"

# Variables necesarias
INSTALL_DIR="/usr/local/bin"
DESTINO_CLI="${INSTALL_DIR}/k3sinstaller"
DESTINO_SH="${INSTALL_DIR}/k3sinstaller.sh"
INS_NAME="k3sinstaller.sh"

RAW_URL_INS="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${INS_NAME}"

# --- VERIFICACIÓN DE PERMISOS ---
if [ "$EUID" -ne 0 ]; then
    echo -e "\n\033[1;31m[X] Error: Este instalador necesita permisos de administrador.\033[0m"
    echo "    Por favor, ejecútalo escribiendo:"
    echo -e "    \033[1;33msudo ./k3sinstallerALL.sh\033[0m\n"
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

echo "Verificando actualizaciones con GitHub..."

# --- DESCARGA DEL ARCHIVO ---
curl -fsSL -o "$DESTINO_CLI" "$RAW_URL_INS"
cp "$DESTINO_CLI" "$DESTINO_SH"

# --- PERMISOS DE EJECUCIÓN ---
chmod +x "$DESTINO_SH"
chmod +x "$DESTINO_CLI"

echo ""
echo "=================================================="
echo " Configurando acceso desde shell..."
echo "=================================================="

# --- FUNCIÓN PARA LIMPIAR Y AGREGAR SOURCE ---
configurar_source() {
    local RC_FILE="$1"
    local USER_NAME="$2"
    
    if [ ! -f "$RC_FILE" ]; then
        return
    fi
    
    # Limpiar líneas previas de source relacionadas con k3sinstaller
    sed -i.bak '/source.*k3sinstaller.sh/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/\. .*k3sinstaller.sh/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/# --- K3s Installer Source ---/d' "$RC_FILE" 2>/dev/null
    
    # Agregar el nuevo source
    cat << 'EOF' >> "$RC_FILE"

# --- K3s Installer Source ---
source /usr/local/bin/k3sinstaller.sh 2>/dev/null || true
EOF
    
    chown "$USER_NAME":"$USER_NAME" "$RC_FILE" 2>/dev/null
    echo "    • Configurado source en: $RC_FILE"
}

# --- DETECTAR SHELL DEL USUARIO Y CONFIGURAR ---
USER_SHELL=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f7)

if [[ "$USER_SHELL" =~ "zsh" ]] || [ -f "$REAL_HOME/.zshrc" ]; then
    configurar_source "$REAL_HOME/.zshrc" "$REAL_USER"
fi

if [ -f "$REAL_HOME/.bashrc" ]; then
    configurar_source "$REAL_HOME/.bashrc" "$REAL_USER"
fi

echo "    • Source agregado automáticamente"
echo ""

# --- EJECUTAR EL INSTALADOR ---
echo "=================================================="
echo " Ejecutando instalador de K3s Manager..."
echo "=================================================="
echo ""

sudo -u "$REAL_USER" "$DESTINO_SH"
