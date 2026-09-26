#!/bin/bash

# --- CONFIGURACIÓN DEL REPOSITORIO ---
GITHUB_USER="braispm9"
REPO_NAME="K3S-Manager"
BRANCH="main"
SCRIPT_NAME="k3smanager.sh"
GUI_SCRIPT_NAME="k3smanager-gui.py"

# Guardado de los scripts en la carpeta actual donde se ejecuta el instalador
DIRECTORIO_ACTUAL="$(cd "$(dirname "$0")" && pwd)"
DESTINO_CLI="${DIRECTORIO_ACTUAL}/${SCRIPT_NAME}"
DESTINO_GUI="${DIRECTORIO_ACTUAL}/${GUI_SCRIPT_NAME}"

echo "====================================================="
echo " Instalador de K3s Manager (CLI & Interfaz Gráfica)"
echo "====================================================="

# 0. Verificar que se ejecute como root o con sudo
if [ "$EUID" -ne 0 ]; then
    echo "   [X] Error crítico: Este script debe ejecutarse obligatoriamente como root o utilizando sudo."
    echo "       Prueba ejecutando: sudo ./k3sinstaller.sh"
    exit 1
fi

# 1. Detectar el usuario real (si se ejecuta con sudo) y su directorio HOME
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(eval echo "~$SUDO_USER")
else
    REAL_USER="$(whoami)"
    REAL_HOME="$HOME"
fi

echo "Instalando para el usuario: $REAL_USER ($REAL_HOME)"

# 2. Comprobar e instalar dependencias básicas del sistema (incluyendo Python y Tkinter)
echo -e "\n1. Verificando dependencias del sistema..."

DEPENDENCIAS=("curl" "fzf" "python3" "python3-tk")
if command -v kubectl &>/dev/null; then
    echo "[OK] Kubernetes"
else
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
    echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
fi

for dep in "${DEPENDENCIAS[@]}"; do
    if ! command -v "$dep" &> /dev/null; then
        echo "   [!] '$dep' no está instalado. Intentando instalar..."
        if command -v apt &> /dev/null; then
            apt update && apt install -y "$dep" || apt install -y python3-tk
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

# 3. Descargar los scripts principales (CLI y GUI) desde GitHub
echo -e "\n2. Descargando scripts desde GitHub..."
RAW_URL_CLI="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${SCRIPT_NAME}"
RAW_URL_GUI="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${GUI_SCRIPT_NAME}"

curl -fsSL -o "$DESTINO_CLI" "$RAW_URL_CLI"
curl -fsSL -o "$DESTINO_GUI" "$RAW_URL_GUI"

if [ $? -eq 0 ] && [ -s "$DESTINO_CLI" ]; then
    echo "   [OK] Script CLI descargado correctamente en: $DESTINO_CLI"
else
    echo "   [X] Error al descargar el script CLI desde GitHub."
    rm -f "$DESTINO_CLI"
    exit 1
fi

if [ -s "$DESTINO_GUI" ]; then
    echo "   [OK] Script GUI descargado correctamente en: $DESTINO_GUI"
else
    echo "   [!] Advertencia: No se pudo descargar la interfaz gráfica (GUI) o no existe aún en el repositorio con ese nombre."
fi

# Ajustar permisos de los scripts descargados
chmod +x "$DESTINO_CLI"
chmod +x "$DESTINO_GUI" 2>/dev/null
chown "$REAL_USER":"$REAL_USER" "$DESTINO_CLI" "$DESTINO_GUI" 2>/dev/null

# 4. Detectar el archivo de configuración (.zshrc o .bashrc) del usuario real
echo -e "\n3. Configurando los alias..."

USER_SHELL=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f7)

if [[ "$USER_SHELL" =~ "zsh" ]] || [ -f "$REAL_HOME/.zshrc" ]; then
    RC_FILE="$REAL_HOME/.zshrc"
else
    RC_FILE="$REAL_HOME/.bashrc"
fi

# Definir los alias: modo CLI y modo Gráfico Independiente con disown
ALIAS_CLI="alias k3smanager='source $DESTINO_CLI'"
ALIAS_GUI="alias k3smanager-gui='python3 \"$DESTINO_GUI\" >/dev/null 2>&1 & disown'"

touch "$RC_FILE"

# Limpiar alias previos si existían para evitar duplicados
if grep -q "alias k3smanager=" "$RC_FILE" 2>/dev/null; then
    sed -i.bak '/alias k3smanager=/d' "$RC_FILE" 2>/dev/null || sed -i '' '/alias k3smanager=/d' "$RC_FILE" 2>/dev/null
fi
if grep -q "alias k3smanager-gui=" "$RC_FILE" 2>/dev/null; then
    sed -i.bak '/alias k3smanager-gui=/d' "$RC_FILE" 2>/dev/null || sed -i '' '/alias k3smanager-gui=/d' "$RC_FILE" 2>/dev/null
fi

echo "" >> "$RC_FILE"
echo "# Aliases K3s Manager" >> "$RC_FILE"
echo "$ALIAS_CLI" >> "$RC_FILE"
echo "$ALIAS_GUI" >> "$RC_FILE"

chown "$REAL_USER" "$RC_FILE" 2>/dev/null

# Cargar k3s como última dependencia si no está presente
if command -v k3s &>/dev/null; then
    echo "[OK] K3S"
else
    curl -sfL https://get.k3s.io | sh -
    sudo chmod 644 /etc/rancher/k3s/k3s.yaml
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
fi

echo "   [OK] Comandos configurados correctamente en $RC_FILE"

echo -e "\n=================================================="
echo " ¡Instalación completada con éxito!"
echo " Para aplicar los cambios inmediatamente ejecuta en tu consola:"
echo "   source $RC_FILE"
echo ""
echo " Comandos disponibles:"
echo "   • k3smanager     -> Ejecuta la versión de consola interactiva"
echo "   • k3smanager-gui -> Abre la interfaz gráfica independiente"
echo "=================================================="
