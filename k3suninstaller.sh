#!/bin/bash

# --- CONFIGURACIÓN DE RUTAS Y COMPONENTES ---
INSTALL_DIR="/usr/local/bin"
DESTINO_CLI="${INSTALL_DIR}/k3smanager"
DESTINO_SH="${INSTALL_DIR}/k3smanager.sh"
DESTINO_GUI="${INSTALL_DIR}/k3smanager-gui"

echo "====================================================="
echo " Desinstalador Completo de K3s Manager (CLI, GUI & Deps)"
echo "====================================================="

# 0. Comprobar privilegios de administrador de forma clara
if [ "$EUID" -ne 0 ]; then
    echo -e "\n\033[1;31m[X] Error: Este desinstalador necesita permisos de administrador.\033[0m"
    echo "    Por favor, ejecútalo escribiendo:"
    echo -e "    \033[1;33msudo ./uninstall.sh\033[0m\n"
    exit 1
fi

# 1. Identificar al usuario real que lanzó el comando con sudo
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(eval echo "~$SUDO_USER")
else
    REAL_USER="$(whoami)"
    REAL_HOME="$HOME"
fi

echo "[i] Desinstalando para el usuario del sistema: $REAL_USER"

# 2. Eliminar binarios globales de K3s Manager
echo -e "\n[1/4] Eliminando binarios y accesos globales..."
rm -f "$DESTINO_CLI"
rm -f "$DESTINO_SH"
rm -f "$DESTINO_GUI"
echo "    • Binarios de CLI y GUI eliminados de $INSTALL_DIR"

# 3. Limpiar configuración y entorno del usuario (.bashrc o .zshrc)
echo -e "\n[2/4] Limpiando accesos directos y variables de entorno..."
USER_SHELL=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f7)

if [[ "$USER_SHELL" =~ "zsh" ]] || [ -f "$REAL_HOME/.zshrc" ]; then
    RC_FILE="$REAL_HOME/.zshrc"
else
    RC_FILE="$REAL_HOME/.bashrc"
fi

if [ -f "$RC_FILE" ]; then
    sed -i.bak '/# --- K3s Manager Shortcuts ---/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/# --- K3s Manager Shortcuts & Environment ---/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/alias k3smanager=/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/alias k3smanager-gui=/d' "$RC_FILE" 2>/dev/null
    sed -i.bak '/export KUBECONFIG/d' "$RC_FILE" 2>/dev/null
    chown "$REAL_USER":"$REAL_USER" "$RC_FILE" 2>/dev/null
    echo "    • Archivo de configuración del shell ($RC_FILE) limpiado."
fi

# Eliminar carpeta .kube generada para el usuario
if [ -d "$REAL_HOME/.kube" ]; then
    rm -rf "$REAL_HOME/.kube"
    echo "    • Directorio de configuración local ($REAL_HOME/.kube) eliminado."
fi

# 4. Desinstalación de dependencias del sistema según el gestor de paquetes (APT / DNF / YUM)
echo -e "\n[3/4] Desinstalación de dependencias del sistema..."
read -p "¿Deseas desinstalar las dependencias instaladas por el manager (fzf, tcpdump, python3-tk/tkinter, etc.)? (s/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    if command -v apt &> /dev/null; then
        echo "    • Detectado sistema Debian/Ubuntu (apt). Desinstalando..."
        apt-get remove -y fzf tcpdump netcat-openbsd iproute2 python3-tk 2>/dev/null
        apt-get autoremove -y 2>/dev/null
    elif command -v dnf &> /dev/null; then
        echo "    • Detectado sistema Fedora (dnf). Desinstalando..."
        dnf remove -y fzf tcpdump nc iproute python3-tkinter 2>/dev/null
    elif command -v yum &> /dev/null; then
        echo "    • Detectado sistema CentOS/RHEL (yum). Desinstalando..."
        yum remove -y fzf tcpdump nc iproute python3-tkinter 2>/dev/null
    else
        echo "    • [Aviso] No se detectó un gestor de paquetes compatible para limpiar dependencias automáticamente."
    fi
    echo "    • Proceso de limpieza de dependencias finalizado."
else
    echo "    • Se omite la desinstalación de dependencias del sistema."
fi

# 5. Preguntar si se desea desinstalar K3s y kubectl del sistema
echo -e "\n[4/4] Desinstalación completa de Kubernetes (Opcional)"
read -p "¿Deseas desinstalar completamente K3s y kubectl del sistema operativo? (s/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    if [ -f /usr/local/bin/k3s-uninstall.sh ]; then
        echo "    • Ejecutando el desinstalador oficial de K3s..."
        /usr/local/bin/k3s-uninstall.sh
    elif command -v k3s-uninstall.sh &> /dev/null; then
        k3s-uninstall.sh
    else
        echo "    • El script oficial de desinstalación de K3s no está disponible, limpiando servicios manualmente..."
        systemctl stop k3s 2>/dev/null
        systemctl disable k3s 2>/dev/null
        rm -f /usr/local/bin/k3s
    fi

    # Eliminar kubectl si se instaló
    if [ -f /usr/local/bin/kubectl ]; then
        rm -f /usr/local/bin/kubectl
        echo "    • kubectl eliminado de /usr/local/bin/"
    fi

    echo "    • K3s y sus servicios han sido removidos."
else
    echo "    • Se omite la desinstalación de K3s. El motor y kubectl se mantienen intactos."
fi

echo -e "\n\033[1;32m==================================================\033[0m"
echo -e "\n\033[1;32m ¡Desinstalación completada con éxito!\033[0m"
echo -e "\n\033[1;32m==================================================\033[0m"
echo "Recuerda reiniciar tu terminal o ejecutar:"
echo -e "  \033[1;33msource $RC_FILE\033[0m"
echo "=================================================="
