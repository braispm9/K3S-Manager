#!/bin/bash

# --- CONFIGURACIÓN DEL REPOSITORIO ---
GITHUB_USER="braispm9"
REPO_NAME="K3S-Manager"
BRANCH="main"
INSTALLER_VERSION="1.6"

SCRIPT_NAME="k3smanager.sh"
GUI_SCRIPT_NAME="k3smanager-gui.py"
# Directorio de instalación global recomendado para scripts ejecutables de usuario
INSTALL_DIR="/usr/local/bin"
DESTINO_SH="${INSTALL_DIR}/k3smanager.sh"
DESTINO_GUI="${INSTALL_DIR}/k3smanager-gui.py"
# Versiones sin extensión (estos son los que se usan en la terminal)
DESTINO_SH_NOEXT="${INSTALL_DIR}/k3smanager"
DESTINO_GUI_NOEXT="${INSTALL_DIR}/k3smanager-gui"

# --- FUNCIÓN PARA MOSTRAR VERSIÓN ---
mostrar_version() {
    echo "====================================================="
    echo " K3s Manager Installer - Versión $INSTALLER_VERSION"
    echo "====================================================="
    echo ""
    echo "Información del Instalador:"
    echo "  • Usuario del repositorio: $GITHUB_USER"
    echo "  • Nombre del repositorio:  $REPO_NAME"
    echo "  • Rama por defecto:        $BRANCH"
    echo ""
    echo "Componentes disponibles:"
    echo "  • CLI (Terminal):  $SCRIPT_NAME"
    echo "  • GUI (Gráfica):   $GUI_SCRIPT_NAME"
    echo ""
    echo "Uso:"
    echo "  • Instalación interactiva: sudo ./k3sinstaller.sh"
    echo "  • Instalar solo CLI:       sudo ./k3sinstaller.sh cli"
    echo "  • Instalar solo GUI:       sudo ./k3sinstaller.sh gui"
    echo "  • Ver versión:             ./k3sinstaller.sh -v"
    echo "  • Ver ayuda:               ./k3sinstaller.sh -h"
    echo ""
}

# --- FUNCIÓN PARA MOSTRAR AYUDA ---
mostrar_ayuda() {
    echo "====================================================="
    echo " K3s Manager Installer - Ayuda"
    echo "====================================================="
    echo ""
    echo "Uso: ./k3sinstaller.sh [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  (sin argumentos)  Instalación interactiva (pregunta qué instalar)"
    echo "  cli               Instala solo la interfaz CLI (terminal)"
    echo "  gui               Instala solo la interfaz GUI (gráfica)"
    echo "  -v, --version     Muestra la versión del instalador"
    echo "  -h, --help        Muestra este mensaje de ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  sudo ./k3sinstaller.sh           # Modo interactivo"
    echo "  sudo ./k3sinstaller.sh cli       # Solo CLI"
    echo "  sudo ./k3sinstaller.sh gui       # Solo GUI"
    echo "  ./k3sinstaller.sh -v             # Ver versión"
    echo ""
}

# --- FUNCIÓN PARA SELECCIONAR MODO INTERACTIVO ---
seleccionar_modo() {
    echo "====================================================="
    echo " Instalador de K3s Manager"
    echo "====================================================="
    echo ""
    echo "¿Qué deseas instalar?"
    echo ""
    echo "  1) CLI (Consola interactiva - terminal)"
    echo "  2) GUI (Interfaz gráfica)"
    echo "  3) Ambos (CLI + GUI)"
    echo "  4) Cancelar"
    echo ""
    read -e -p "Selecciona una opción (1-4): " opcion
    
    case $opcion in
        1)
            INSTALL_MODE="cli"
            ;;
        2)
            INSTALL_MODE="gui"
            ;;
        3)
            INSTALL_MODE="both"
            ;;
        4)
            echo "Instalación cancelada."
            exit 0
            ;;
        *)
            echo "Opción no válida. Por favor, selecciona 1, 2, 3 o 4."
            seleccionar_modo
            ;;
    esac
}

# --- FUNCIÓN PARA LIMPIAR INSTALACIONES PREVIAS ---
limpiar_previos() {
    echo -e "\n\033[1;33m[!] Limpiando instalaciones previas de K3s Manager...\033[0m"

    # Eliminar archivos de instalación anteriores (con extensión)
    if [ -f "$DESTINO_SH" ]; then
        rm -f "$DESTINO_SH"
        echo "    • Eliminado: $DESTINO_SH"
    fi

    if [ -f "$DESTINO_GUI" ]; then
        rm -f "$DESTINO_GUI"
        echo "    • Eliminado: $DESTINO_GUI"
    fi

    # Eliminar versiones sin extensión
    if [ -f "$DESTINO_SH_NOEXT" ]; then
        rm -f "$DESTINO_SH_NOEXT"
        echo "    • Eliminado: $DESTINO_SH_NOEXT"
    fi

    if [ -f "$DESTINO_GUI_NOEXT" ]; then
        rm -f "$DESTINO_GUI_NOEXT"
        echo "    • Eliminado: $DESTINO_GUI_NOEXT"
    fi

    # Limpiar archivos de historial y temporales del usuario
    if [ -f "$REAL_HOME/.k3smanager_history" ]; then
        rm -f "$REAL_HOME/.k3smanager_history"
        echo "    • Eliminado historial: $REAL_HOME/.k3smanager_history"
    fi

    # Eliminar conexion.log y monitor_connect.log si existen
    if [ -f "$REAL_HOME/conexion.log" ]; then
        rm -f "$REAL_HOME/conexion.log"
        echo "    • Eliminado: $REAL_HOME/conexion.log"
    fi

    if [ -f "$REAL_HOME/monitor_connect.log" ]; then
        rm -f "$REAL_HOME/monitor_connect.log"
        echo "    • Eliminado: $REAL_HOME/monitor_connect.log"
    fi

    # Limpiar los aliases de .bashrc y .zshrc
    USER_SHELL=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f7)

    if [[ "$USER_SHELL" =~ "zsh" ]] || [ -f "$REAL_HOME/.zshrc" ]; then
        if [ -f "$REAL_HOME/.zshrc" ]; then
            sed -i.bak '/alias k3smanager=/d' "$REAL_HOME/.zshrc" 2>/dev/null
            sed -i.bak '/alias k3smanager-gui=/d' "$REAL_HOME/.zshrc" 2>/dev/null
            sed -i.bak '/export KUBECONFIG/d' "$REAL_HOME/.zshrc" 2>/dev/null
            sed -i.bak '/# --- K3s Manager Shortcuts & Environment ---/d' "$REAL_HOME/.zshrc" 2>/dev/null
            echo "    • Limpiados alias de: $REAL_HOME/.zshrc"
        fi
    fi

    if [ -f "$REAL_HOME/.bashrc" ]; then
        sed -i.bak '/alias k3smanager=/d' "$REAL_HOME/.bashrc" 2>/dev/null
        sed -i.bak '/alias k3smanager-gui=/d' "$REAL_HOME/.bashrc" 2>/dev/null
        sed -i.bak '/export KUBECONFIG/d' "$REAL_HOME/.bashrc" 2>/dev/null
        sed -i.bak '/# --- K3s Manager Shortcuts & Environment ---/d' "$REAL_HOME/.bashrc" 2>/dev/null
        echo "    • Limpiados alias de: $REAL_HOME/.bashrc"
    fi

    echo -e "\033[1;32m[OK] Limpieza completada.\033[0m\n"
}

# --- FUNCIÓN PARA INSTALAR DEPENDENCIAS ---
instalar_dependencias() {
    echo -e "[1/4] Verificando e instalando dependencias del sistema..."

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
}

# --- FUNCIÓN PARA INSTALAR K3S Y KUBECTL ---
instalar_kubernetes() {
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
}

# --- FUNCIÓN PARA CONFIGURAR RED ---
configurar_red() {
    echo -e "\n[i] Configurando reenvío de IP y reglas de red/firewall para K3s..."
    # Habilitar IP Forwarding en el Kernel
    sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1
    if ! grep -q "net.ipv4.ip_forward" /etc/sysctl.conf; then
        echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    else
        sed -i 's/#*net.ipv4.ip_forward=.*/net.ipv4.ip_forward=1/' /etc/sysctl.conf
    fi
    sysctl -p /etc/sysctl.conf >/dev/null 2>&1

    # Ajustes específicos de Firewall según la distribución detectada
    if command -v firewall-cmd &> /dev/null && systemctl is-active --quiet firewalld; then
        echo "    • Configurando firewalld (Fedora/RHEL) para permitir interfaces de contenedores..."
        firewall-cmd --permanent --add-interface=cni0 >/dev/null 2>&1
        firewall-cmd --permanent --add-interface=flannel.1 >/dev/null 2>&1
        firewall-cmd --permanent --zone=trusted --add-interface=cni0 >/dev/null 2>&1
        firewall-cmd --permanent --zone=trusted --add-interface=flannel.1 >/dev/null 2>&1
        firewall-cmd --reload >/dev/null 2>&1
    elif command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
        echo "    • Ajustando política de reenvío en UFW (Debian/Ubuntu)..."
        sed -i 's/DEFAULT_FORWARD_POLICY="DROP"/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw 2>/dev/null
        ufw reload >/dev/null 2>&1
    fi
}

# --- FUNCIÓN PARA CONFIGURAR KUBECONFIG ---
configurar_kubeconfig() {
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
}

# --- FUNCIÓN PARA DESCARGAR E INSTALAR COMPONENTES ---
descargar_componentes() {
    echo -e "\n[3/4] Descargando componentes desde el repositorio..."
    RAW_URL_CLI="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${SCRIPT_NAME}"
    RAW_URL_GUI="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${GUI_SCRIPT_NAME}"

    # Instalar CLI si es requerido
    if [ "$INSTALL_MODE" == "cli" ] || [ "$INSTALL_MODE" == "both" ]; then
        curl -fsSL -o "$DESTINO_SH" "$RAW_URL_CLI"

        if [ -s "$DESTINO_SH" ]; then
            chmod +x "$DESTINO_SH"
            chown "$REAL_USER":"$REAL_USER" "$DESTINO_SH"
            # Crear versión sin extensión que apunte al script con extensión
            cp "$DESTINO_SH" "$DESTINO_SH_NOEXT"
            chmod +x "$DESTINO_SH_NOEXT"
            chown "$REAL_USER":"$REAL_USER" "$DESTINO_SH_NOEXT"
            echo "    • Componente CLI instalado en: $DESTINO_SH_NOEXT (y $DESTINO_SH)"
        else
            echo -e "\n\033[1;31m[X] Error: No se pudo descargar el script CLI desde GitHub.\033[0m"
            exit 1
        fi
    fi

    # Instalar GUI si es requerido
    if [ "$INSTALL_MODE" == "gui" ] || [ "$INSTALL_MODE" == "both" ]; then
        curl -fsSL -o "$DESTINO_GUI" "$RAW_URL_GUI"

        if [ -s "$DESTINO_GUI" ]; then
            chmod +x "$DESTINO_GUI"
            chown "$REAL_USER":"$REAL_USER" "$DESTINO_GUI"
            # Crear versión sin extensión que apunte al script Python
            cp "$DESTINO_GUI" "$DESTINO_GUI_NOEXT"
            chmod +x "$DESTINO_GUI_NOEXT"
            chown "$REAL_USER":"$REAL_USER" "$DESTINO_GUI_NOEXT"
            echo "    • Componente GUI instalado en: $DESTINO_GUI_NOEXT (y $DESTINO_GUI)"
        else
            echo "    • [Aviso] La interfaz gráfica (GUI) no se pudo descargar."
        fi
    fi
}

# --- FUNCIÓN PARA CONFIGURAR ALIASES ---
configurar_aliases() {
    echo -e "\n[4/4] Configurando accesos directos..."
    USER_SHELL=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f7)

    if [[ "$USER_SHELL" =~ "zsh" ]] || [ -f "$REAL_HOME/.zshrc" ]; then
        RC_FILE="$REAL_HOME/.zshrc"
    else
        RC_FILE="$REAL_HOME/.bashrc"
    fi

    # Escribir accesos directos y la variable KUBECONFIG en el entorno del usuario
    # Ya no necesitan alias porque los comandos sin extensión están en /usr/local/bin
    cat << 'EOF' >> "$RC_FILE"

# --- K3s Manager Shortcuts & Environment ---
export KUBECONFIG="$HOME/.kube/config"
EOF

    chown "$REAL_USER":"$REAL_USER" "$RC_FILE" 2>/dev/null
}

# --- FUNCIÓN PARA MOSTRAR MENSAJE FINAL ---
mensaje_final() {
    echo -e "\n\033[1;32m==================================================\033[0m"
    echo -e "\033[1;32m ¡Instalación completada con éxito!\033[0m"
    echo -e "\n\033[1;32m==================================================\033[0m"
    echo "Ya puedes utilizar la herramienta abriendo una nueva terminal"
    echo "o ejecutando inmediatamente en tu consola actual:"
    echo -e "  \033[1;33msource $RC_FILE\033[0m"
    echo ""
    echo "Componentes instalados:"
    
    if [ "$INSTALL_MODE" == "cli" ] || [ "$INSTALL_MODE" == "both" ]; then
        echo "  • Consola interactiva : k3smanager"
    fi
    
    if [ "$INSTALL_MODE" == "gui" ] || [ "$INSTALL_MODE" == "both" ]; then
        echo "  • Interfaz Gráfica    : k3smanager-gui"
    fi
    
    echo "=================================================="
}

# --- MAIN: ANÁLISIS DE ARGUMENTOS ---
if [ $# -gt 0 ]; then
case "${1:-}" in
    -v|--version)
        echo "K3s Manager Installer - Versión ${INSTALLER_VERSION}"
        exit 0
        ;;
    -h|--help)
        echo "Uso: $0 [cli|gui|-v|--version|-h|--help]"
        echo ""
        echo "  Sin argumentos       Instalación interactiva"
        echo "  cli                  Instalar solo CLI"
        echo "  gui                  Instalar solo GUI"
        echo "  -v, --version        Mostrar versión sin instalar"
        echo "  -h, --help           Mostrar ayuda"
        exit 0
        ;;
esac
else
    # Modo interactivo si no hay argumentos
    seleccionar_modo
fi

# --- COMPROBAR PRIVILEGIOS ---
if [ "$EUID" -ne 0 ]; then
    echo -e "\n\033[1;31m[X] Error: Este instalador necesita permisos de administrador.\033[0m"
    echo "    Por favor, ejecútalo escribiendo:"
    echo -e "    \033[1;33msudo ./k3sinstaller.sh\033[0m\n"
    exit 1
fi

# --- IDENTIFICAR USUARIO REAL ---
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(eval echo "~$SUDO_USER")
else
    REAL_USER="$(whoami)"
    REAL_HOME="$HOME"
fi

echo "[i] Instalando para el usuario del sistema: $REAL_USER"

# --- EJECUTAR INSTALACIÓN ---
limpiar_previos
instalar_dependencias
instalar_kubernetes
configurar_red
configurar_kubeconfig
descargar_componentes
configurar_aliases
mensaje_final
