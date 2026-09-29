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

#Verificando si hay nueva actualizacion de k3sinstaller
if [ -n "$ZSH_VERSION" ]; then
    SCRIPT_ACTUAL="${(%):-%x}"
else
    SCRIPT_ACTUAL="${BASH_SOURCE[0]:-$0}"
fi

#Permisos de ejecucion

echo "Verificando actualizaciones con GitHub..."
if [ "$EUID" -ne 0 ]; then
    echo -e "\n\033[1;31m[X] Error: Este instalador necesita permisos de administrador.\033[0m"
    echo "    Por favor, ejecútalo escribiendo:"
    echo -e "    \033[1;33msudo ./install.sh\033[0m\n"
    exit 1
fi

# Descarga del archivos
curl -fsSL -o "$DESTINO_CLI" "$RAW_URL_INS"
cp "$DESTINO_CLI" "$DESTINO_SH"

# Ejecución del archivo
chmod 777 "$DESTINO_SH"
sudo "$DESTINO_SH"

