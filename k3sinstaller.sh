#!/bin/bash

# --- CONFIGURATION ---
GITHUB_USER="braispm9"; REPO_NAME="K3S-Manager"; BRANCH="main"
SCRIPT_NAME="k3smanager.sh"; GUI_SCRIPT_NAME="k3smanager-gui.py"; INSTALLER_VERSION="2.4"
INSTALL_DIR="/usr/local/bin"
DESTINO_CLI="${INSTALL_DIR}/k3smanager"
DESTINO_SH="${INSTALL_DIR}/k3smanager.sh"
DESTINO_GUI="${INSTALL_DIR}/k3smanager-gui"
DESTINO_UNINSTALLER="${INSTALL_DIR}/k3suninstaller.sh"
SELF_PATH="$(readlink -f "$0")"

show_version() {
    cat << EOF
=====================================================
 K3s Manager Master Installer - Version $INSTALLER_VERSION
=====================================================
Repository User: $GITHUB_USER | Repo: $REPO_NAME | Branch: $BRANCH
EOF
}

show_help() {
    cat << EOF
=====================================================
 K3s Manager Master Installer - Help
=====================================================
Usage: sudo ./k3sinstallerALL.sh [OPTION]
  (no args)       Interactive management menu
  -u, --verify-update  Check for remote updates
  -v              Show version
  -h              Show help
EOF
}

# --- CHECK FOR UPDATES ---
verify_update() {
    echo "Checking for remote updates from GitHub - 721v"
    REMOTE_VERSION_URL="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/k3sinstallerALL.sh"
    
    # Download remote header version temporarily to compare
    REMOTE_CONTENT=$(curl -fsSL "$REMOTE_VERSION_URL" 2>/dev/null)
    if [ -z "$REMOTE_CONTENT" ]; then
        echo "Failed to reach GitHub repository for update check - 721x"
        return 1
    fi
    
    REMOTE_VERSION=$(echo "$REMOTE_CONTENT" | grep -m 1 "INSTALLER_VERSION=" | cut -d'"' -f2)
    
    if [ "$REMOTE_VERSION" != "$INSTALLER_VERSION" ] && [ -n "$REMOTE_VERSION" ]; then
        echo "New version available: v$REMOTE_VERSION (Current: v$INSTALLER_VERSION) - 722v"
        read -e -p "Do you want to update now? (y/n): " choice
        if [[ "$choice" =~ ^[Yy]$ ]]; then
            echo "$REMOTE_CONTENT" > "$SELF_PATH"
            chmod +x "$SELF_PATH"
            echo "Installer updated successfully. Please re-run it. - 723v"
            exit 0
        fi
    else
        echo "Installer is already up to date (v$INSTALLER_VERSION) - 724v"
    fi
}

select_mode() {
    echo "====================================================="
    echo " K3s Manager Management Menu"
    echo "====================================================="
    echo "1) Install CLI only"
    echo "2) Install GUI (includes CLI)"
    echo "3) Update Installer itself"
    echo "4) Update / Redownload component files"
    echo "5) Remove installers, scripts & aliases only"
    echo "6) Complete purge (Remove everything including K3s)"
    echo "7) Cancel"
    echo "====================================================="
    read -e -p "Select option (1-7): " opcion
    case $opcion in
        1) INSTALL_MODE="cli" ;;
        2) INSTALL_MODE="gui" ;;
        3) update_self && exit 0 ;;
        4) update_files && exit 0 ;;
        5) remove_installers_and_aliases && exit 0 ;;
        6) complete_purge && exit 0 ;;
        7) echo "Operation cancelled. - 100v" && exit 0 ;;
        *) echo "Invalid option. Please try again. - 100x" && select_mode ;;
    esac
}

# --- UPDATE INSTALLER ITSELF ---
update_self() {
    echo "Updating installer script from GitHub - 701v"
    # Añadimos ?v=$(date +%s) para evitar que GitHub sirva una versión en caché
    RAW_URL_INSTALLER="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/k3sinstallerALL.sh?v=$(date +%s)"
    
    if curl -fsSL "$RAW_URL_INSTALLER" -o "$SELF_PATH"; then
        chmod +x "$SELF_PATH"
        echo "Installer successfully updated. Please re-run it. - 702v"
    else
        echo "Failed to update installer from repository. - 701x"
        exit 1
    fi
}

# --- UPDATE COMPONENT FILES ---
update_files() {
    echo "Updating component files from GitHub - 711v"
    RAW_URL_CLI="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${SCRIPT_NAME}"
    RAW_URL_GUI="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${GUI_SCRIPT_NAME}"
    
    curl -fsSL -o "$DESTINO_CLI" "$RAW_URL_CLI" && cp "$DESTINO_CLI" "$DESTINO_SH"
    curl -fsSL -o "$DESTINO_GUI" "$RAW_URL_GUI"
    
    chmod +x "$DESTINO_CLI" "$DESTINO_SH" "$DESTINO_GUI" 2>/dev/null
    echo "Component files successfully updated. - 712v"
}

# --- REMOVE INSTALLERS, SCRIPTS & ALIASES ---
remove_installers_and_aliases() {
    echo "Cleaning up installers, scripts, and shell aliases - 801v"
    rm -f "$DESTINO_CLI" "$DESTINO_SH" "$DESTINO_GUI" "${DESTINO_GUI}.py" "$DESTINO_UNINSTALLER" \
          "$REAL_HOME/.k3smanager_history" "$REAL_HOME/conexion.log" "$REAL_HOME/monitor_connect.log"
    
    for rc_file in "$REAL_HOME/.zshrc" "$REAL_HOME/.bashrc"; do
        if [ -f "$rc_file" ]; then
            sed -i.bak -e '/alias k3smanager=/d' -e '/alias k3smanager-gui=/d' -e '/export KUBECONFIG/d' -e '/# --- K3s Manager Shortcuts & Environment ---/d' "$rc_file" 2>/dev/null
        fi
    done
    echo "Installers and aliases removed successfully. - 802v"
}

# --- COMPLETE PURGE (INCLUDING K3S) ---
complete_purge() {
    echo "Executing complete system purge including K3s - 901v"
    if [ -f /usr/local/bin/k3s-uninstall.sh ]; then
        /usr/local/bin/k3s-uninstall.sh >/dev/null 2>&1
    elif [ -f /usr/bin/k3s-uninstall.sh ]; then
        /usr/bin/k3s-uninstall.sh >/dev/null 2>&1
    fi
    systemctl stop k3s >/dev/null 2>&1
    systemctl disable k3s >/dev/null 2>&1
    rm -rf /etc/rancher /var/lib/rancher ~/.kube
    remove_installers_and_aliases
    echo "Complete system purge finished. - 902v"
}

# --- CLEAN PREVIOUS INSTALLATIONS ---
clean_installation() {
    remove_installers_and_aliases
}

# --- DEPENDENCIES & KUBERNETES ---
install_dependencies() {
    echo "Checking Kubernetes components"
    
    if ! command -v kubectl &> /dev/null; then
        echo "Installing kubectl - 201v"
        curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && rm -f kubectl || { echo "kubectl install failed - 201x"; exit 1; }
    else
        echo "kubectl already installed - 202v"
    fi
    
    echo "Installing & Updating K3s local server - 203v"
    curl -sfL https://get.k3s.io | sh - || echo "Official installer warning/failed - 203x"
    
    if [ ! -f /etc/systemd/system/k3s.service ]; then
        echo "Creating K3s systemd unit - 204v"
        cat << 'EOF' > /etc/systemd/system/k3s.service
[Unit]
Description=Lightweight Kubernetes
Documentation=https://k3s.io
After=network-online.target

[Service]
Type=notify
ExecStart=/usr/local/bin/k3s server
KillMode=process
Delegate=yes
LimitNOFILE=1048576
LimitNPROC=infinity
LimitCORE=infinity
TasksMax=infinity
TimeoutStartSec=0
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF
    fi
    
    systemctl daemon-reload && systemctl enable --now k3s >/dev/null 2>&1 && echo "K3s service started - 205v" || { echo "K3s service failed - 205x"; exit 1; }
}

# --- NETWORK & FIREWALL ---
network_config() {
    echo "Configuring IP forwarding and firewall rules"

    sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1
    if ! grep -q "net.ipv4.ip_forward" /etc/sysctl.conf; then
        echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    else
        sed -i 's/#*net.ipv4.ip_forward=.*/net.ipv4.ip_forward=1/' /etc/sysctl.conf
    fi
    sysctl -p /etc/sysctl.conf >/dev/null 2>&1 && echo "IP forwarding enabled - 301v" || { echo "IP forwarding failed - 301x"; exit 1; }
    
    if command -v firewall-cmd &> /dev/null && systemctl is-active --quiet firewalld; then
        echo "Configuring firewalld rules - 302v"
        firewall-cmd --permanent --add-interface=cni0 >/dev/null 2>&1
        firewall-cmd --permanent --add-interface=flannel.1 >/dev/null 2>&1
        firewall-cmd --permanent --zone=trusted --add-interface=cni0 >/dev/null 2>&1
        firewall-cmd --permanent --zone=trusted --add-interface=flannel.1 >/dev/null 2>&1
        firewall-cmd --reload >/dev/null 2>&1 && echo "Firewalld configured - 302v" || { echo "Firewalld configuration failed - 302x"; exit 1; }
    elif command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
        echo "Configuring UFW rules - 303v"
        sed -i 's/DEFAULT_FORWARD_POLICY="DROP"/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw 2>/dev/null
        ufw reload >/dev/null 2>&1 && echo "UFW configured - 303v" || { echo "UFW configuration failed - 303x"; exit 1; }
    fi
}

# --- KUBECONFIG PERMISSIONS ---
kubeconfig_config() {
    echo "Configuring non-root user access to Kubernetes for $REAL_USER"

    local intentos=0
    while [ ! -f /etc/rancher/k3s/k3s.yaml ] && [ $intentos -lt 15 ]; do
        sleep 1
        intentos=$((intentos + 1))
    done

    if [ -f /etc/rancher/k3s/k3s.yaml ]; then
        mkdir -p "$REAL_HOME/.kube"
        cp /etc/rancher/k3s/k3s.yaml "$REAL_HOME/.kube/config"
        chown -R "$REAL_USER":"$REAL_USER" "$REAL_HOME/.kube"
        chmod 600 "$REAL_HOME/.kube/config"
        chmod +x /etc/rancher 2>/dev/null
        chmod +rx /etc/rancher/k3s 2>/dev/null
        echo "Kubeconfig successfully configured - 351v"
    else
        echo "Warning: Kubeconfig file not found. Check status with 'sudo systemctl status k3s' - 351x"
    fi
}

# --- DOWNLOAD COMPONENTS ---
components_download() {
    RAW_URL_CLI="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${SCRIPT_NAME}"
    RAW_URL_GUI="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${GUI_SCRIPT_NAME}"
    
    if [ "$INSTALL_MODE" == "cli" ]; then
        echo "Downloading CLI component - 401v"
        curl -fsSL -o "$DESTINO_CLI" "$RAW_URL_CLI" && cp "$DESTINO_CLI" "$DESTINO_SH"
    
        if [ -s "$DESTINO_CLI" ]; then
            chmod +x "$DESTINO_CLI" "$DESTINO_SH"
            chown "$REAL_USER":"$REAL_USER" "$DESTINO_CLI" "$DESTINO_SH"
            echo "CLI component installed - 402v"
        else
            echo "CLI download failed - 401x"
            exit 1
        fi
    elif [ "$INSTALL_MODE" == "gui" ]; then
        echo "Downloading CLI & GUI components - 403v"
        curl -fsSL -o "$DESTINO_CLI" "$RAW_URL_CLI" && cp "$DESTINO_CLI" "$DESTINO_SH"
        curl -fsSL -o "$DESTINO_GUI" "$RAW_URL_GUI"
    
        if [ -s "$DESTINO_CLI" ]; then
            chmod +x "$DESTINO_CLI" "$DESTINO_SH"
            chown "$REAL_USER":"$REAL_USER" "$DESTINO_CLI" "$DESTINO_SH"
            echo "CLI component installed - 402v"
        fi

        if [ -s "$DESTINO_GUI" ]; then
            chmod +x "$DESTINO_GUI"
            chown "$REAL_USER":"$REAL_USER" "$DESTINO_GUI"
            echo "GUI component installed - 404v"
        else
            echo "GUI download failed or not published - 403x"
        fi
    fi
}

# --- SHELL ALIASES & ENVIRONMENT ---
alias_config() {
    USER_SHELL=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f7)
    
    if [[ "$USER_SHELL" =~ "zsh" ]] || [ -f "$REAL_HOME/.zshrc" ]; then
        RC_FILE="$REAL_HOME/.zshrc"
    else
        RC_FILE="$REAL_HOME/.bashrc"
    fi
    
    echo "Configuring shortcuts and environment - 501v"
    
    if [ "$INSTALL_MODE" == "cli" ]; then
        cat << 'EOF' >> "$RC_FILE"

# --- K3s Manager Shortcuts & Environment ---
export KUBECONFIG="$HOME/.kube/config"
alias k3smanager='k3smanager'
EOF
    elif [ "$INSTALL_MODE" == "gui" ]; then
        cat << 'EOF' >> "$RC_FILE"

# --- K3s Manager Shortcuts & Environment ---
export KUBECONFIG="$HOME/.kube/config"
alias k3smanager='k3smanager'
alias k3smanager-gui='nohup python3 /usr/local/bin/k3smanager-gui > "$HOME/k3s_gui_error.log" 2>&1 & disown'
EOF
    fi
    
    chown "$REAL_USER":"$REAL_USER" "$RC_FILE" 2>/dev/null && echo "Shortcuts configured - 501v" || { echo "Shortcuts configuration failed - 501x"; exit 1; }
}

# --- FINAL SUCCESS MESSAGE ---
final_message() {
    echo "Installation completed successfully - 601v"
    echo "You can now use the tool by opening a new terminal or running:"
    echo "source $RC_FILE"
    
    if [ "$INSTALL_MODE" == "cli" ]; then
        echo "CLI Component installed - 602v"
    elif [ "$INSTALL_MODE" == "gui" ]; then
        echo "CLI Component installed - 602v"
        echo "GUI Component installed - 603v"
    fi
}

# --- EXECUTION FLOW ---

# Ensure root privileges first
if [ "$EUID" -ne 0 ]; then
    echo "Administrator privileges required - 101x"
    echo "Please run: sudo ./k3sinstallerALL.sh"
    exit 1
fi

# Handle command-line options
if [ $# -gt 0 ]; then
    case "${1:-}" in
        -v|--version)
            show_version
            exit 0
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--verify-update)
            verify_update
            exit 0
            ;;
        cli)
            INSTALL_MODE="cli"
            ;;
        gui)
            INSTALL_MODE="gui"
            ;;
    esac
else
    # Automatically verify updates on startup when no arguments are passed
    verify_update
    echo ""
    select_mode
fi

# Resolve real system user (avoiding root home issues)
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(eval echo "~$SUDO_USER")
else
    REAL_USER="$(whoami)"
    REAL_HOME="$HOME"
fi

echo "Installing for system user: $REAL_USER - 102v"

# Run full installation pipeline
clean_installation
install_dependencies
network_config
kubeconfig_config
components_download
alias_config
final_message
