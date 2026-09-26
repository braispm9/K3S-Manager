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
echo "    • Binarios de CLI y GUI eliminados de $INSTALL_DIR"[cite: 6]

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
    echo "    • Archivo de configuración del shell ($RC_FILE) limpiado."[cite: 6]
fi

# Eliminar carpeta .kube generada para el usuario
if [ -d "$REAL_HOME/.kube" ]; then
    rm -rf "$REAL_HOME/.kube"
    echo "    • Directorio de configuración local ($REAL_HOME/.kube) eliminado."[cite: 6]
fi

# 4. Desinstalación de dependencias del sistema según el gestor de paquetes (APT / DNF / YUM)
echo -e "\n[3/4] Desinstalación de dependencias del sistema..."
read -p "¿Deseas desinstalar las dependencias instaladas por el manager (fzf, tcpdump, python3-tk/tkinter, etc.)? (s/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    if command -v apt &> /dev/null; then
        echo "    • Detectado sistema Debian/Ubuntu (apt). Desinstalando..."[cite: 6]
        apt-get remove -y fzf tcpdump netcat-openbsd iproute2 python3-tk 2>/dev/null
        apt-get autoremove -y 2>/dev/null
    elif command -v dnf &> /dev/null; then
        echo "    • Detectado sistema Fedora (dnf). Desinstalando..."[cite: 6]
        dnf remove -y fzf tcpdump nc iproute python3-tkinter 2>/dev/null
    elif command -v yum &> /dev/null; then
        echo "    • Detectado sistema CentOS/RHEL (yum). Desinstalando..."[cite: 6]
        yum remove -y fzf tcpdump nc iproute python3-tkinter 2>/dev/null
    else
        echo "    • [Aviso] No se detectó un gestor de paquetes compatible para limpiar dependencias automáticamente."[cite: 6]
    fi
    echo "    • Proceso de limpieza de dependencias finalizado."[cite: 6]
else
    echo "    • Se omite la desinstalación de dependencias del sistema."[cite: 6]
fi

# 5. Preguntar si se desea desinstalar K3s, kubectl y revertir configuraciones de red
echo -e "\n[4/4] Desinstalación completa de Kubernetes y configuración de red (Opcional)"
read -p "¿Deseas desinstalar completamente K3s, kubectl y revertir los cambios de red del kernel/firewall? (s/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    if [ -f /usr/local/bin/k3s-uninstall.sh ]; then
        echo "    • Ejecutando el desinstalador oficial de K3s..."[cite: 6]
        /usr/local/bin/k3s-uninstall.sh
    elif command -v k3s-uninstall.sh &> /dev/null; then
        k3s-uninstall.sh
    else
        echo "    • El script oficial de desinstalación de K3s no está disponible, limpiando servicios manualmente..."[cite: 6]
        systemctl stop k3s 2>/dev/null
        systemctl disable k3s 2>/dev/null
        rm -f /usr/local/bin/k3s
    fi

    # Eliminar kubectl si se instaló
    if [ -f /usr/local/bin/kubectl ]; then
        rm -f /usr/local/bin/kubectl
        echo "    • kubectl eliminado de /usr/local/bin/"[cite: 6]
    fi

    # Revertir configuraciones de red (IP Forwarding y Firewall)
    echo "    • Revirtiendo ajustes de red y reenvío IP..."
    sed -i '/net.ipv4.ip_forward=1/d' /etc/sysctl.conf 2>/dev/null
    sysctl -w net.ipv4.ip_forward=0 >/dev/null 2>&1

    if command -v firewall-cmd &> /dev/null && systemctl is-active --quiet firewalld; then
        firewall-cmd --permanent --remove-interface=cni0 >/dev/null 2>&1
        firewall-cmd --permanent --remove-interface=flannel.1 >/dev/null 2>&1
        firewall-cmd --reload >/dev/null 2>&1
        echo "    • Reglas de firewalld limpiadas."
    elif command -v ufw &> /dev/null; then
        sed -i 's/DEFAULT_FORWARD_POLICY="ACCEPT"/DEFAULT_FORWARD_POLICY="DROP"/' /etc/default/ufw 2>/dev/null
        ufw reload >/dev/null 2>&1
        echo "    • Política de reenvío de UFW restaurada."
    fi

    echo "    • K3s, sus servicios y configuraciones de red han sido removidos."[cite: 6]
else
    echo "    • Se omite la desinstalación de K3s. El motor y kubectl se mantienen intactos."[cite: 6]
fi

echo -e "\n\033[1;32m==================================================\033[0m"
echo -e "\n\033[1;32m ¡Desinstalación completada con éxito!\033[0m"
echo -e "\n\033[1;32m==================================================\033[0m"
echo "Recuerda reiniciar tu terminal o ejecutar:"
echo -e "  \033[1;33msource $RC_FILE\033[0m"
echo "=================================================="[cite: 6]
