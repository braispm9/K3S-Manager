#!/bin/bash

# --- CONFIGURACIÓN DEL REPOSITORIO ---
GITHUB_USER="braispm9"
REPO_NAME="K3S-Manager"
BRANCH="main"
SCRIPT_NAME="k3smanager.sh"
GUI_SCRIPT_NAME="k3smanager-gui.py"

# Directorio de instalación global recomendado para scripts ejecutables de usuario
INSTALL_DIR="/usr/local/bin"
DESTINO_CLI="${INSTALL_DIR}/k3smanager"
DESTINO_SH="${INSTALL_DIR}/k3smanager.sh"
DESTINO_GUI="${INSTALL_DIR}/k3smanager-gui"

echo "====================================================="
echo " Instalador Definitivo de K3s Manager (CLI & GUI)"
echo "====================================================="

# 0. Comprobar privilegios de administrador de forma clara
if [ "$EUID" -ne 0 ]; then
    echo -e "\n\033[1;31m[X] Error: Este instalador necesita permisos de administrador.\033[0m"
    echo "    Por favor, ejecútalo escribiendo:"
    echo -e "    \033[1;33msudo ./install.sh\033[0m\n"
    exit 1
fi

# 1. Identificar al usuario real que lanzó el comando con sudo (evita instalar todo en /root/)
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(eval echo "~$SUDO_USER")
else
    REAL_USER="$(whoami)"
    REAL_HOME="$HOME"
fi

echo "[i] Instalando para el usuario del sistema: $REAL_USER"

# 2. Detección del sistema e instalación automática de dependencias
echo -e "\n[1/4] Verificando e instalando dependencias del sistema..."

UTILS_DEBIAN="curl fzf tcpdump netcat-openbsd iproute2 python3 python3-tk"
UTILS_FEDORA="curl fzf tcpdump nc iproute python3 python3-tkinter"

if command -v apt &> /dev/null; then
    echo "    • Sistema basado en Debian/Ubuntu detectado (apt)."
    apt-get update -qq
    apt-get install -y $UTILS_DEBIAN
elif command -v dnf &> /dev/null; then
    echo "    • Sistema basado en Fedora detectado (dnf)."
    dnf install -y $UTILS_FEDORA
elif command -v yum &> /dev/null; then
    echo "    • Sistema basado en CentOS/RHEL detectado (yum)."
    yum install -y $UTILS_FEDORA
else
    echo -e "\n\033[1;31m[X] No se pudo detectar un gestor de paquetes compatible (apt, dnf, yum).\033[0m"
    exit 1
fi

# 3. Asegurar kubectl y K3s
echo -e "\n[2/4] Verificando Kubernetes (K3s y kubectl)..."
if ! command -v kubectl &> /dev/null; then
    echo "    • Instalando kubectl..."
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    rm -f kubectl
else
    echo "    • kubectl ya está instalado."
fi

if ! command -v k3s &> /dev/null; then
    echo "    • K3s no detectado. Instalando K3s servidor local..."
    curl -sfL https://get.k3s.io | sh -
else
    echo "    • K3s ya está instalado en este nodo."
fi

# --- CONFIGURACIÓN ROBUSTA DE PERMISOS Y KUBECONFIG PARA USUARIO NORMAL ---
echo -e "\n[i] Configurando acceso sin sudo a Kubernetes para el usuario $REAL_USER..."
if [ -f /etc/rancher/k3s/k3s.yaml ]; then
    # Crear la carpeta .kube en el directorio personal del usuario real
    mkdir -p "$REAL_HOME/.kube"

    # Copiar el archivo de configuración de K3s al directorio del usuario
    cp /etc/rancher/k3s/k3s.yaml "$REAL_HOME/.kube/config"

    # Ajustar propietario y permisos estrictos requeridos por kubectl (600)
    chown -R "$REAL_USER":"$REAL_USER" "$REAL_HOME/.kube"
    chmod 600 "$REAL_HOME/.kube/config"

    # Asegurar permisos globales básicos en /etc/rancher por si acaso
    chmod +x /etc/rancher 2>/dev/null
    chmod +rx /etc/rancher/k3s 2>/dev/null

    echo "    • Kubeconfig copiado y configurado en '$REAL_HOME/.kube/config' (Acceso OK sin sudo)."
fi


# 4. Descargar los scripts directamente desde GitHub a la ruta global
echo -e "\n[3/4] Descargando componentes desde el repositorio..."
RAW_URL_CLI="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${SCRIPT_NAME}"
RAW_URL_GUI="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${GUI_SCRIPT_NAME}"

curl -fsSL -o "$DESTINO_CLI" "$RAW_URL_CLI"
cp "$DESTINO_CLI" "$DESTINO_SH"
curl -fsSL -o "$DESTINO_GUI" "$RAW_URL_GUI"

if [ -s "$DESTINO_CLI" ]; then
    chmod +x "$DESTINO_CLI"
    chmod +x "$DESTINO_SH"
    chown "$REAL_USER":"$REAL_USER" "$DESTINO_CLI"
    chown "$REAL_USER":"$REAL_USER" "$DESTINO_SH"
    echo "    • Componente CLI instalado en: $DESTINO_CLI"
else
    echo -e "\n\033[1;31m[X] Error: No se pudo descargar el script CLI desde GitHub.\033[0m"
    exit 1
fi

if [ -s "$DESTINO_GUI" ]; then
    chmod +x "$DESTINO_GUI"
    chown "$REAL_USER":"$REAL_USER" "$DESTINO_GUI"
    echo "    • Componente GUI instalado en: $DESTINO_GUI"
else
    echo "    • [Aviso] La interfaz gráfica (GUI) no se pudo descargar o aún no está publicada."
fi


# 5. Configuración automática del entorno del usuario (.bashrc o .zshrc)
echo -e "\n[4/4] Configurando accesos directos..."
USER_SHELL=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f7)

if [[ "$USER_SHELL" =~ "zsh" ]] || [ -f "$REAL_HOME/.zshrc" ]; then
    RC_FILE="$REAL_HOME/.zshrc"
else
    RC_FILE="$REAL_HOME/.bashrc"
fi

# Limpieza previa de configuraciones previas si existieran
if [ -f "$RC_FILE" ]; then
    sed -i.bak '/alias k3smanager=/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/alias k3smanager-gui=/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/export KUBECONFIG/d' "$RC_FILE" 2>/dev/null
fi

# Escribir accesos directos y la variable KUBECONFIG en el entorno del usuario
cat << 'EOF' >> "$RC_FILE"

# --- K3s Manager Shortcuts & Environment ---
export KUBECONFIG="$HOME/.kube/config"
alias k3smanager='k3smanager'
alias k3smanager-gui='python3 /usr/local/bin/k3smanager-gui >/dev/null 2>&1 & disown'
EOF

chown "$REAL_USER":"$REAL_USER" "$RC_FILE" 2>/dev/null

echo -e "\n\033[1;32m==================================================\033[0m"
echo -e "\033[1;32m ¡Instalación completada con éxito!\033[0m"
echo -e "\n\033[1;32m==================================================\033[0m"
echo "Ya puedes utilizar la herramienta abriendo una nueva terminal"
echo "o ejecutando inmediatamente en tu consola actual:"
echo -e "  \033[1;33msource $RC_FILE\033[0m"
echo ""
echo "Comandos disponibles desde cualquier lugar:"
echo "  • Consola interactiva : k3smanager"
echo "  • Interfaz Gráfica    : k3smanager-gui"
echo "=================================================="
