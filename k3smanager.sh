#!/bin/bash
VERSION="Release 3.2"
if [ "$REINICIANDO_K3SMANAGER" = true ]; then
    unset REINICIANDO_K3SMANAGER
fi
export PROMPT="k3s> "

# --- FUNCIONES DE AYUDA Y CONSOLA INTERACTIVA ---

mostrar_ayuda() {
    local cmd="$1"

    if [ -z "$cmd" ]; then
        echo -e "\nComandos disponibles para Pods:"
        echo "  pods [ID|N-M|namespace|-A] - Listar pods con ID estricto (ej: pods, pods 1, pods 1-50)"
        echo "  add pod <IDs...>           - Añadir pod(s) por su ID numérico asignado (ej: add pod 1 10)"
        echo "  remove pod <IDs...>        - Quitar pod(s) de la selección activa (ej: remove pod 1)"
        echo "  clear-sel                  - Limpiar toda la selección de pods actual"
        echo "  clear                      - Limpiar la pantalla de la terminal"
        echo "  show                       - Mostrar pods seleccionados actualmente"
        echo ""
        echo "Comandos de información y acción:"
        echo "  ip <ID | nombre> [ns]      - Obtener la IP interna de un pod por su ID o nombre"
        echo "  describe [-l]              - Ver información resumida o completa (-l) de la selección"
        echo "  logs                       - Mostrar logs (requiere seleccionar solo 1 pod)"
        echo "  delete                     - Eliminar el/los pod(s) seleccionados"
        echo "  create <N|N-M> [-i imagen] - Crea pod individual o rango con imagen opcional"
        echo ""
        echo "Pruebas de Red, Control de Puertos y Auditoría:"
        echo "  check-ports [ID | N-M]     - Escanea los puertos abiertos de pods seleccionados o por ID/rango"
        echo "  close-port <ID|N-M>        - Bloquea el tráfico de red de un pod por NetworkPolicy"
        echo "  open-port <ID|N-M>         - Restablece el tráfico de red eliminando la NetworkPolicy"
        echo "  monitor-connect            - Monitoriza accesos a TODOS los puertos abiertos en monitor_connect.log"
        echo "  test-network [N | N-M |-a] - Crear y probar conectividad hacia pods específicos o todos"
        echo "  test-connections [orig dest] - Probar tráfico directo entre dos pods por su ID"
        echo ""
        echo "  version                    - Verifica si es la última versión y muestra la versión actual"
        echo "  update                     - Instala la última versión del software y se reactiva"
        echo "  help [comando]             - Ayuda general o de una función específica"
        echo -e "  exit | quit                - Salir de la consola\n"
        return
    fi

    case $cmd in
        pods|list)
            echo -e "\nUSO: pods [ID | N-M | namespace | -n namespace | -A]"
            echo "Muestra los pods disponibles asignando un ID numérico único correlativo (1, 2, 3...)."
            ;;
        check-ports)
            echo -e "\nUSO: check-ports [ID | N-M]"
            echo "Escanea y muestra los puertos abiertos en los pods indicados o seleccionados."
            ;;
        close-port)
            echo -e "\nUSO: close-port <ID | N-M>"
            echo "Aplica una NetworkPolicy para aislar y bloquear el tráfico entrante al pod especificado."
            ;;
        open-port)
            echo -e "\nUSO: open-port <ID | N-M>"
            echo "Elimina el aislamiento por NetworkPolicy del pod, volviendo a permitir la comunicación."
            ;;
        monitor-connect)
            echo -e "\nUSO: monitor-connect"
            echo "Detecta dinámicamente todos los puertos TCP en escucha (LISTEN) en la máquina host."
            echo "Captura en tiempo real todos los intentos de conexión TCP (SYN) entrantes."
            echo "Omite automáticamente el tráfico de loopback (127.0.0.1) y la subred K3s (10.42.0.0/16)."
            echo "Guarda la actividad con marca de tiempo e IP formateada en 'monitor_connect.log'."
            ;;
        ip)
            echo -e "\nUSO: ip <ID_numérico | nombre_pod> [namespace]"
            echo "Muestra la dirección IP asignada al pod mediante su ID numérico."
            ;;
        create)
            echo -e "\nUSO: create <N | N-M> [--image <imagen> | -i <imagen>]"
            echo "Crea pods de prueba individuales o por rango."
            ;;
        describe)
            echo -e "\nUSO: describe [-l]"
            echo "Muestra la información de los pods seleccionados mediante sus IDs."
            ;;
        test-network)
            echo -e "\nUSO: test-network [N | N-M | -a | --all]"
            echo "Crea y mide conectividad hacia los pods especificados por su número (1 al 50)."
            ;;
        test-connections)
            echo -e "\nUSO: test-connections [ID_ORIGEN] [ID_DESTINO]"
            echo "Realiza una petición HTTP entre dos pods identificados por sus IDs numéricos."
            ;;
        clear)
            echo -e "\nUSO: clear"
            echo "Limpia la pantalla de la terminal."
            ;;
        *)
            echo -e "\nNo hay información detallada sobre '$cmd'. Escribe 'help' para ver la lista.\n"
            ;;
    esac
}

comprobar_actualizacion() {
    GITHUB_USER="braispm9"
    REPO_NAME="K3S-Manager"
    BRANCH="main"
    SCRIPT_NAME="k3smanager.sh"

    echo "Verificando actualizaciones con GitHub..."

    if [ -n "$ZSH_VERSION" ]; then
        SCRIPT_ACTUAL="${(%):-%x}"
    else
        SCRIPT_ACTUAL="${BASH_SOURCE[0]:-$0}"
    fi
    RUTA_LOCAL="$(readlink -f "$SCRIPT_ACTUAL" 2>/dev/null || realpath "$SCRIPT_ACTUAL" 2>/dev/null || echo "$SCRIPT_ACTUAL")"

    TEMP_REMOTE=$(mktemp)
    RAW_URL="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${SCRIPT_NAME}?t=$(date +%s)"

    if curl -fsSL -H "Cache-Control: no-cache" -o "$TEMP_REMOTE" "$RAW_URL"; then
        HASH_LOCAL=$(sha256sum "$RUTA_LOCAL" 2>/dev/null | awk '{print $1}' || md5sum "$RUTA_LOCAL" 2>/dev/null | awk '{print $1}')
        HASH_REMOTO=$(sha256sum "$TEMP_REMOTE" 2>/dev/null | awk '{print $1}' || md5sum "$TEMP_REMOTE" 2>/dev/null | awk '{print $1}')

        rm -f "$TEMP_REMOTE"

        if [ -n "$HASH_LOCAL" ] && [ "$HASH_LOCAL" = "$HASH_REMOTO" ]; then
            echo "   [OK] Estás utilizando la última versión disponible."
        else
            echo "   [!] Hay una nueva versión disponible en GitHub."
            echo "       Ejecuta 'update' para actualizar el script."
        fi
    else
        rm -f "$TEMP_REMOTE"
        echo "   [X] No se pudo conectar con GitHub para verificar la versión."
    fi
}

actualizar_k3smanager() {
    echo "=========================================="
    echo " Actualizando K3s Manager desde GitHub..."
    echo "=========================================="

    GITHUB_USER="braispm9"
    REPO_NAME="K3S-Manager"
    BRANCH="main"
    SCRIPT_NAME="k3smanager.sh"

    API_URL="https://api.github.com/repos/${GITHUB_USER}/${REPO_NAME}/contents/${SCRIPT_NAME}?ref=${BRANCH}"

    if [ -n "$ZSH_VERSION" ]; then
        ORIGEN="${(%):-%x}"
    else
        ORIGEN="${BASH_SOURCE[0]:-$0}"
    fi

    RUTA_DESTINO="$(readlink -f "$ORIGEN" 2>/dev/null || realpath "$ORIGEN" 2>/dev/null || echo "$ORIGEN")"
    TEMP_FILE=$(mktemp)

    if curl -fsSL -H "Accept: application/vnd.github.v3.raw" -H "Cache-Control: no-cache" -o "$TEMP_FILE" "$API_URL"; then
        if [ -s "$TEMP_FILE" ]; then
            mv "$TEMP_FILE" "$RUTA_DESTINO"
            chmod +x "$RUTA_DESTINO"
            echo "   [OK] Versión descargada correctamente."
            echo "=========================================="
            return 0
        else
            echo "   [X] Error: El archivo recibido está vacío."
            rm -f "$TEMP_FILE"
            return 1
        fi
    else
        echo "   [X] Error al conectar con la API de GitHub."
        rm -f "$TEMP_FILE"
        return 1
    fi
}

actualizar_pods() {
    PODS_LIST=()
    PODS_NS_LIST=()

    while read -r ns name; do
        if [ -n "$name" ] && [ "$ns" != "kube-system" ]; then
            PODS_NS_LIST+=("$ns")
            PODS_LIST+=("$name")
        fi
    done < <(kubectl get pods --all-namespaces --no-headers -o custom-columns="NS:.metadata.namespace,NAME:.metadata.name" 2>/dev/null | sort -k2 -V)
}

listar_pods_pantalla() {
    local arg1="$1"
    local arg2="$2"
    local ns_filtro=""
    local inicio=0
    local fin=0

    actualizar_pods

    if [ ${#PODS_LIST[@]} -eq 0 ]; then
        echo "No se encontraron pods de aplicación disponibles."
        return
    fi

    if [[ "$arg1" =~ ^[0-9]+$ ]]; then
        inicio=$arg1
        fin=$arg1
    elif [[ "$arg1" =~ ^([0-9]+)-([0-9]+)$ ]]; then
        inicio="${BASH_REMATCH[1]}"
        fin="${BASH_REMATCH[2]}"
    elif [ "$arg1" == "-A" ] || [ "$arg1" == "--all-namespaces" ]; then
        ns_filtro=""
    elif [ "$arg1" == "-n" ]; then
        ns_filtro="$arg2"
    else
        ns_filtro="$arg1"
    fi

    local contador_impresos=0
    echo -e "\nID   NAMESPACE        NOMBRE DEL POD"
    echo "--------------------------------------------------"

    for i in "${!PODS_LIST[@]}"; do
        local id_actual=$((i + 1))
        local current_ns="${PODS_NS_LIST[$i]}"
        local current_pod="${PODS_LIST[$i]}"

        if [ "$inicio" -gt 0 ]; then
            if [ "$id_actual" -ge "$inicio" ] && [ "$id_actual" -le "$fin" ]; then
                printf "%-4d %-17s %s\n" "$id_actual" "$current_ns" "$current_pod"
                contador_impresos=$((contador_impresos + 1))
            fi
        else
            if [ -z "$ns_filtro" ] || [ "$current_ns" == "$ns_filtro" ]; then
                printf "%-4d %-17s %s\n" "$id_actual" "$current_ns" "$current_pod"
                contador_impresos=$((contador_impresos + 1))
            fi
        fi
    done

    if [ $contador_impresos -eq 0 ]; then
        if [ "$inicio" -gt 0 ]; then
            echo "No se encontraron pods en el rango especificado ($inicio - $fin)."
        else
            echo "No se encontraron pods en el namespace '$ns_filtro'."
        fi
    else
        echo ""
    fi
}

obtener_pods_por_indice() {
    local ids=("$@")
    PODS_TEMPORALES=()
    NS_TEMPORALES=()

    actualizar_pods

    for id in "${ids[@]}"; do
        if [[ "$id" =~ ^[0-9]+$ ]] && [ "$id" -ge 1 ] && [ "$id" -le "${#PODS_LIST[@]}" ]; then
            idx=$((id - 1))
            PODS_TEMPORALES+=("${PODS_LIST[$idx]}")
            NS_TEMPORALES+=("${PODS_NS_LIST[$idx]}")
        else
            echo "Error: El ID '$id' no es válido. Revisa los IDs con el comando 'pods'."
            return 1
        fi
    done
}

obtener_ip_pod() {
    local target=$(echo "$1" | tr -d '"' | tr -d "'")
    local pod_ns_param=$(echo "$2" | tr -d '"' | tr -d "'")

    if [ -z "$target" ]; then
        echo "Uso: ip <ID_o_Nombre> [namespace]"
        return 1
    fi

    actualizar_pods

    local pod_nombre=""
    local pod_ns=""

    if [[ "$target" =~ ^[0-9]+$ ]]; then
        if [ "$target" -ge 1 ] && [ "$target" -le "${#PODS_LIST[@]}" ]; then
            local idx=$((target - 1))
            pod_nombre="${PODS_LIST[$idx]}"
            pod_ns="${PODS_NS_LIST[$idx]}"
        else
            echo "Error: El ID '$target' no existe en la lista general."
            return 1
        fi
    else
        pod_nombre="$target"

        if [ -n "$pod_ns_param" ]; then
            pod_ns="$pod_ns_param"
        else
            pod_ns=$(kubectl get pod -A --no-headers -o custom-columns="NS:.metadata.namespace,NAME:.metadata.name" 2>/dev/null | grep -w "$pod_nombre" | awk '{print $1}' | head -n 1)
        fi
    fi

    if [ -z "$pod_ns" ]; then
        echo "Error: No se encontró el pod '$pod_nombre'."
        return 1
    fi

    local ip=$(kubectl get pod "$pod_nombre" -n "$pod_ns" -o jsonpath='{.status.podIP}' 2>/dev/null)
    local status=$(kubectl get pod "$pod_nombre" -n "$pod_ns" -o jsonpath='{.status.phase}' 2>/dev/null)

    if [ -n "$ip" ]; then
        echo -e "IP del Pod ID/Nombre '$target' -> [$pod_nombre] (NS: \033[1;34m${pod_ns}\033[0m | Estado: \033[1;33m${status}\033[0m): \033[1;32m$ip\033[0m"
    else
        echo "Error: El pod '$pod_nombre' existe en '$pod_ns' (Estado: ${status:-Desconocido}), pero no tiene IP asignada."
        return 1
    fi
}

añadir_a_seleccion() {
    if obtener_pods_por_indice "$@"; then
        for i in "${!PODS_TEMPORALES[@]}"; do
            local pod="${PODS_TEMPORALES[$i]}"
            local ns="${NS_TEMPORALES[$i]}"
            local existe=0

            for j in "${!SELECCIONADOS_PODS[@]}"; do
                if [ "${SELECCIONADOS_PODS[$j]}" == "$pod" ] && [ "${SELECCIONADOS_NAMESPACES[$j]}" == "$ns" ]; then
                    existe=1
                    break
                fi
            done

            if [ $existe -eq 0 ]; then
                SELECCIONADOS_PODS+=("$pod")
                SELECCIONADOS_NAMESPACES+=("$ns")
                echo "Pod ID/Nombre '$pod' (namespace: $ns) añadido a la selección."
            else
                echo "El pod '$pod' ya estaba seleccionado."
            fi
        done
    fi
}

quitar_de_seleccion() {
    if obtener_pods_por_indice "$@"; then
        for i in "${!PODS_TEMPORALES[@]}"; do
            local pod_quitar="${PODS_TEMPORALES[$i]}"
            local ns_quitar="${NS_TEMPORALES[$i]}"
            NUEVA_PODS=()
            NUEVA_NS=()

            for j in "${!SELECCIONADOS_PODS[@]}"; do
                if [ "${SELECCIONADOS_PODS[$j]}" != "$pod_quitar" ] || [ "${SELECCIONADOS_NAMESPACES[$j]}" != "$ns_quitar" ]; then
                    NUEVA_PODS+=("${SELECCIONADOS_PODS[$j]}")
                    NUEVA_NS+=("${SELECCIONADOS_NAMESPACES[$j]}")
                fi
            done

            SELECCIONADOS_PODS=("${NUEVA_PODS[@]}")
            SELECCIONADOS_NAMESPACES=("${NUEVA_NS[@]}")
            echo "Pod '$pod_quitar' removido de la selección."
        done
    fi
}

# --- CONTROL Y BLOQUEO DE PUERTOS/RED ---

cerrar_puerto_pod() {
    local arg="$1"
    local target_pods=()
    local target_ns=()

    actualizar_pods

    if [[ "$arg" =~ ^[0-9]+$ ]]; then
        if [ "$arg" -ge 1 ] && [ "$arg" -le "${#PODS_LIST[@]}" ]; then
            local idx=$((arg - 1))
            target_pods+=("${PODS_LIST[$idx]}")
            target_ns+=("${PODS_NS_LIST[$idx]}")
        fi
    elif [[ "$arg" =~ ^([0-9]+)-([0-9]+)$ ]]; then
        local inicio="${BASH_REMATCH[1]}"
        local fin="${BASH_REMATCH[2]}"
        for ((i=inicio; i<=fin; i++)); do
            if [ "$i" -ge 1 ] && [ "$i" -le "${#PODS_LIST[@]}" ]; then
                local idx=$((i - 1))
                target_pods+=("${PODS_LIST[$idx]}")
                target_ns+=("${PODS_NS_LIST[$idx]}")
            fi
        done
    elif [ ${#SELECCIONADOS_PODS[@]} -gt 0 ]; then
        target_pods=("${SELECCIONADOS_PODS[@]}")
        target_ns=("${SELECCIONADOS_NAMESPACES[@]}")
    fi

    if [ ${#target_pods[@]} -eq 0 ]; then
        echo "Error: Especifica un ID (ej: close-port 1), un rango (ej: close-port 1-50) o selecciona pods previamente."
        return 1
    fi

    for i in "${!target_pods[@]}"; do
        local pod="${target_pods[$i]}"
        local ns="${target_ns[$i]}"
        local netpol_name="block-ingress-${pod}"

        kubectl label pod "$pod" -n "$ns" "k3smanager-isolated=true" --overwrite >/dev/null 2>&1

        cat <<EOF | kubectl apply -f - >/dev/null 2>&1
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ${netpol_name}
  namespace: ${ns}
spec:
  podSelector:
    matchLabels:
      k3smanager-isolated: "true"
  policyTypes:
  - Ingress
EOF

        if [ $? -eq 0 ]; then
            echo -e "\033[1;32m[OK]\033[0m Aislamiento de red/puertos aplicado exitosamente en '\033[1;36m$pod\033[0m' (NS: $ns)."
        else
            echo -e "\033[1;31m[X]\033[0m Error al aplicar la NetworkPolicy en '$pod'."
        fi
    done
}

abrir_puerto_pod() {
    local arg="$1"
    local target_pods=()
    local target_ns=()

    actualizar_pods

    if [[ "$arg" =~ ^[0-9]+$ ]]; then
        if [ "$arg" -ge 1 ] && [ "$arg" -le "${#PODS_LIST[@]}" ]; then
            local idx=$((arg - 1))
            target_pods+=("${PODS_LIST[$idx]}")
            target_ns+=("${PODS_NS_LIST[$idx]}")
        fi
    elif [[ "$arg" =~ ^([0-9]+)-([0-9]+)$ ]]; then
        local inicio="${BASH_REMATCH[1]}"
        local fin="${BASH_REMATCH[2]}"
        for ((i=inicio; i<=fin; i++)); do
            if [ "$i" -ge 1 ] && [ "$i" -le "${#PODS_LIST[@]}" ]; then
                local idx=$((i - 1))
                target_pods+=("${PODS_LIST[$idx]}")
                target_ns+=("${PODS_NS_LIST[$idx]}")
            fi
        done
    elif [ ${#SELECCIONADOS_PODS[@]} -gt 0 ]; then
        target_pods=("${SELECCIONADOS_PODS[@]}")
        target_ns=("${SELECCIONADOS_NAMESPACES[@]}")
    fi

    if [ ${#target_pods[@]} -eq 0 ]; then
        echo "Error: Especifica un ID (ej: open-port 1), un rango (ej: open-port 1-50) o selecciona pods previamente."
        return 1
    fi

    for i in "${!target_pods[@]}"; do
        local pod="${target_pods[$i]}"
        local ns="${target_ns[$i]}"
        local netpol_name="block-ingress-${pod}"

        kubectl delete networkpolicy "$netpol_name" -n "$ns" >/dev/null 2>&1
        kubectl label pod "$pod" -n "$ns" "k3smanager-isolated-" >/dev/null 2>&1

        echo -e "\033[1;32m[OK]\033[0m Bloqueo removido. Tráfico reactivado en '\033[1;36m$pod\033[0m' (NS: $ns)."
    done
}

# --- AUDITORÍA DE CONEXIONES EN PUERTOS ABIERTOS ---

monitorizar_conexiones() {
    local log_file="monitor_connect.log"

    if ! command -v tcpdump &> /dev/null; then
        echo -e "\033[1;31m[X] Error: 'tcpdump' no está instalado en el sistema.\033[0m"
        echo "Instálalo ejecutando: sudo apt update && sudo apt install -y tcpdump"
        return 1
    fi

    echo -e "\n\033[1;36m[+] Escaneando puertos abiertos en el sistema host...\033[0m"

    local open_ports=()
    if command -v ss &> /dev/null; then
        open_ports=($(ss -tuln | awk '{print $5}' | grep -oE '[0-9]+$' | sort -u))
    elif command -v netstat &> /dev/null; then
        open_ports=($(netstat -tuln | awk '{print $4}' | grep -oE '[0-9]+$' | sort -u))
    fi

    if [ ${#open_ports[@]} -eq 0 ]; then
        echo -e "\033[1;33m[!] No se detectaron puertos en LISTEN. Se aplicará captura general TCP.\033[0m"
        filter_ports="tcp"
    else
        echo -e "\033[1;32m[OK] Puertos abiertos detectados:\033[0m ${open_ports[*]}"
        local ports_str=""
        for p in "${open_ports[@]}"; do
            ports_str="${ports_str}port $p or "
        done
        filter_ports="tcp and (${ports_str% or })"
    fi

    echo -e "\n\033[1;36m[+] Monitorizando intentos de acceso SYN a puertos abiertos...\033[0m"
    echo -e "Filtro activo: Excluyendo subred K3s (10.42.0.0/16) y localhost (127.0.0.1)"
    echo -e "Registrando eventos en '\033[1;33m$log_file\033[0m'."
    echo -e "Presiona \033[1;31mCtrl+C\033[0m para salir del modo auditoría.\n"

    # Captura mejorada con exclusión nativa de red interna/Pods y localhost
    sudo tcpdump -i any -n -e -l "tcp[tcpflags] & tcp-syn != 0 and ($filter_ports) and not src net 10.42.0.0/16 and not src 127.0.0.1" 2>/dev/null | \
    while read -r line; do
        local ips=($(echo "$line" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}\.[0-9]+'))

        if [ ${#ips[@]} -ge 2 ]; then
            ip_origen="${ips[0]%.*}"
            puerto_destino="${ips[1]##*.}"

            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            registro="[$timestamp] IP Origen: $ip_origen | Puerto Destino: $puerto_destino"

            echo -e "\033[1;32m[CONEXIÓN DETECTADA]\033[0m $registro"
            echo "$registro" >> "$log_file"
        fi
    done
}

# --- ESCANEO DE PUERTOS Y SERVICIOS ---

mapear_servicio_puerto() {
    local port="$1"
    case "$port" in
        80|8080|8000) echo "HTTP" ;;
        443|8443)    echo "HTTPS" ;;
        6379)        echo "Redis" ;;
        5432)        echo "PostgreSQL" ;;
        3306)        echo "MySQL/MariaDB" ;;
        27017)       echo "MongoDB" ;;
        53)          echo "DNS" ;;
        22)          echo "SSH" ;;
        *)           echo "Desconocido/Custom" ;;
    esac
}

escanear_puertos_pod() {
    local arg="$1"
    local pods_a_escanear=()
    local ns_a_escanear=()

    actualizar_pods

    if [[ "$arg" =~ ^[0-9]+$ ]]; then
        if [ "$arg" -ge 1 ] && [ "$arg" -le "${#PODS_LIST[@]}" ]; then
            local idx=$((arg - 1))
            pods_a_escanear+=("${PODS_LIST[$idx]}")
            ns_a_escanear+=("${PODS_NS_LIST[$idx]}")
        else
            echo "Error: El ID '$arg' está fuera del rango de pods existente."
            return 1
        fi
    elif [[ "$arg" =~ ^([0-9]+)-([0-9]+)$ ]]; then
        local inicio="${BASH_REMATCH[1]}"
        local fin="${BASH_REMATCH[2]}"

        if [ "$inicio" -lt 1 ] || [ "$fin" -gt 50 ] || [ "$inicio" -gt "$fin" ]; then
            echo "Error: El rango especificado ($inicio-$fin) debe estar entre 1 y 50."
            return 1
        fi

        for ((i=inicio; i<=fin; i++)); do
            if [ "$i" -le "${#PODS_LIST[@]}" ]; then
                local idx=$((i - 1))
                pods_a_escanear+=("${PODS_LIST[$idx]}")
                ns_a_escanear+=("${PODS_NS_LIST[$idx]}")
            fi
        done
    elif [ ${#SELECCIONADOS_PODS[@]} -gt 0 ]; then
        pods_a_escanear=("${SELECCIONADOS_PODS[@]}")
        ns_a_escanear=("${SELECCIONADOS_NAMESPACES[@]}")
    else
        echo "Error: Indica un ID (ej: check-ports 1), un rango (ej: check-ports 1-50) o selecciona pods previamente con 'select'."
        return 1
    fi

    echo -e "\nIniciando escaneo de puertos en ${#pods_a_escanear[@]} pod(s)...\n"

    local puertos_comunes=(80 443 8080 8000 6379 5432 3306 27017 53 22 8443)

    for i in "${!pods_a_escanear[@]}"; do
        local pod="${pods_a_escanear[$i]}"
        local ns="${ns_a_escanear[$i]}"

        local ip=$(kubectl get pod "$pod" -n "$ns" -o jsonpath='{.status.podIP}' 2>/dev/null)
        local status=$(kubectl get pod "$pod" -n "$ns" -o jsonpath='{.status.phase}' 2>/dev/null)

        echo -e "\033[1;36m[POD]\033[0m $pod (NS: $ns | Estado: $status | IP: ${ip:-N/A})"

        if [ -z "$ip" ] || [ "$status" != "Running" ]; then
            echo "   \033[1;31m[X] Imposible escanear: el pod no está en ejecución o no tiene IP asignada.\033[0m"
            echo "------------------------------------------------------------------"
            continue
        fi

        for port in "${puertos_comunes[@]}"; do
            (
                if nc -z -w 1 "$ip" "$port" 2>/dev/null || (echo > "/dev/tcp/$ip/$port") 2>/dev/null; then
                    local srv=$(mapear_servicio_puerto "$port")
                    echo -e "   \033[1;32m[+] Puerto $port/TCP ABIERTO\033[0m -> Servicio: \033[1;33m$srv\033[0m"
                fi
            ) &
        done
        wait

        local puertos_spec=$(kubectl get pod "$pod" -n "$ns" -o jsonpath='{.spec.containers[*].ports[*].containerPort}' 2>/dev/null)
        if [ -n "$puertos_spec" ]; then
            echo -e "   \033[1;34m[*] Puertos expuestos según manifiesto:\033[0m $puertos_spec"
        fi

        echo "------------------------------------------------------------------"
    done
}

# --- FUNCIONES DE EVALUACIÓN Y CONEXIONES DE RED ---

probar_red_cluster() {
    local arg="$1"
    local inicio=1
    local fin=50

    if [[ "$arg" =~ ^[0-9]+$ ]]; then
        fin=$arg
    elif [[ "$arg" =~ ^([0-9]+)-([0-9]+)$ ]]; then
        inicio="${BASH_REMATCH[1]}"
        fin="${BASH_REMATCH[2]}"
    elif [ "$arg" == "-a" ] || [ "$arg" == "--all" ]; then
        inicio=1
        fin=50
    fi

    if [ "$inicio" -lt 1 ] || [ "$fin" -gt 50 ] || [ "$inicio" -gt "$fin" ]; then
        echo "Error: Indica un número o rango válido entre 1 y 50 (ej: test-network 1-2)."
        return 1
    fi

    local total_maquinas=$((fin - inicio + 1))
    echo "Creando/verificando $total_maquinas pod(s) de prueba (rango: $inicio a $fin)..."

    for ((i=inicio; i<=fin; i++)); do
        if ! kubectl get pod "pod-prueba-$i" -A >/dev/null 2>&1; then
            kubectl run "pod-prueba-$i" --image=nginx:alpine --port=80 >/dev/null 2>&1
        fi
    done

    echo "Esperando a que los pods estén listos..."
    for ((i=inicio; i<=fin; i++)); do
        kubectl wait --for=condition=Ready "pod/pod-prueba-$i" --timeout=15s >/dev/null 2>&1
    done

    echo "Lanzando contenedor probador de red..."
    kubectl run probador-red --image=curlimages/curl --restart=Never -- sleep 3600 >/dev/null 2>&1
    kubectl wait --for=condition=Ready pod/probador-red --timeout=10s >/dev/null 2>&1

    echo -e "\nProbando comunicación con los pods del $inicio al $fin...\n"
    ERRORES=0
    rm -f conexion.log >/dev/null 2>&1

    for ((i=inicio; i<=fin; i++)); do
        IP_POD=$(kubectl get pod -A --no-headers -o custom-columns="NAME:.metadata.name,IP:.status.podIP" 2>/dev/null | grep -w "pod-prueba-$i" | awk '{print $2}')

        if [ -n "$IP_POD" ]; then
            STATUS=$(kubectl exec probador-red -- curl -s -o /dev/null -w "%{http_code}" "http://$IP_POD" 2>/dev/null)
        else
            STATUS="SIN_IP"
        fi

        if [ "$STATUS" -ne 200 ] 2>/dev/null; then
            echo "[X] Pod pod-prueba-$i (IP: ${IP_POD:-N/A}) Error de conexión (HTTP ${STATUS})" >> conexion.log
            ERRORES=$((ERRORES + 1))
        fi
    done

    if [ $ERRORES -gt 0 ]; then
        echo -e "[X] Se encontraron $ERRORES errores de conexión."
        echo "Verifica el archivo conexion.log para detalles."
    else
        echo -e "[OK] ¡Comunicaciones exitosas con los $total_maquinas pods especificados!\n"

        read -e -p "¿Deseas cargar automáticamente estos pods en la selección? (s/n): " opcion
        if [[ "$opcion" =~ ^[sS]$ ]]; then
            actualizar_pods
            for idx in "${!PODS_LIST[@]}"; do
                for ((k=inicio; k<=fin; k++)); do
                    if [ "${PODS_LIST[$idx]}" == "pod-prueba-$k" ]; then
                        añadir_a_seleccion "$((idx + 1))" >/dev/null
                    fi
                done
            done
            echo "Pods del rango importados a la selección activa."
        fi
    fi

    kubectl delete pod probador-red --grace-period=0 --force >/dev/null 2>&1
}

probar_conexion_entre_pods() {
    local id_orig="$1"
    local id_dest="$2"

    if [ -z "$id_orig" ] || [ -z "$id_dest" ]; then
        echo "Error: Debes especificar el ID de origen y destino. Ejemplo: test-connections 1 2"
        return 1
    fi

    if obtener_pods_por_indice "$id_orig" "$id_dest"; then
        local pod_origen="${PODS_TEMPORALES[0]}"
        local ns_origen="${NS_TEMPORALES[0]}"
        local pod_destino="${PODS_TEMPORALES[1]}"
        local ns_destino="${NS_TEMPORALES[1]}"

        local ip_destino=$(kubectl get pod "$pod_destino" -n "$ns_destino" -o jsonpath='{.status.podIP}' 2>/dev/null)

        if [ -z "$ip_destino" ]; then
            echo "Error: No se pudo obtener la IP del pod destino '$pod_destino'."
            return 1
        fi

        echo -e "\nProbando conectividad desde '$pod_origen' ($ns_origen) hacia '$pod_destino' ($ip_destino)..."

        RESPUESTA=$(kubectl exec -n "$ns_origen" "$pod_origen" -- sh -c "curl -s -m 3 http://$ip_destino || wget -qO- -T 3 http://$ip_destino" 2>&1)
        EXIT_CODE=$?

        if [ $EXIT_CODE -eq 0 ] && [ -n "$RESPUESTA" ]; then
            echo -e "[OK] Conexión exitosa. Respuesta recibida del pod destino:\n"
            echo "$RESPUESTA" | head -n 10
        else
            echo -e "[X] Error de conexión hacia $ip_destino:"
            echo "$RESPUESTA"
            echo -e "\nTip: Si el pod de origen es una imagen muy reducida sin 'curl' ni 'wget', la ejecución fallará localmente en el contenedor."
        fi
    fi
}

HISTFILE=~/.k3smanager_history
HISTSIZE=1000
SAVEHIST=1000

# --- BUCLE PRINCIPAL (TERMINAL INTERACTIVA) ---

echo "=================================================="
echo " Consola Interactiva K3s (Gestión de Pods)"
echo " Escribe 'help' o 'help <comando>' para asistencia."
echo "=================================================="

actualizar_pods

while true; do
    PROMPT="${PROMPT:-k3s> }"

    if [ -n "$BASH_VERSION" ]; then
        set -o history
        read -e -r -p "$PROMPT" ENTRADA_RAW
    elif [ -n "$ZSH_VERSION" ]; then
        read -r "ENTRADA_RAW?$PROMPT"
    else
        read -r -p "$PROMPT" ENTRADA_RAW
    fi

    [ -z "$ENTRADA_RAW" ] && continue

    if [ -n "$BASH_VERSION" ]; then
        history -s "$ENTRADA_RAW" 2>/dev/null
    fi

    read -r -a INPUT <<< "$ENTRADA_RAW"
    COMANDO="${INPUT[0]}"
    SUBACCION="${INPUT[1]}"
    ARGUMENTOS=("${INPUT[@]:1}")

    case "$COMANDO" in
        list|pods)
            listar_pods_pantalla "$SUBACCION" "${INPUT[2]}"
            ;;

        check-ports)
            escanear_puertos_pod "$SUBACCION"
            ;;

        close-port)
            cerrar_puerto_pod "$SUBACCION"
            ;;

        open-port)
            abrir_puerto_pod "$SUBACCION"
            ;;

        monitor-connect)
            monitorizar_conexiones
            ;;

        ip|get-ip)
            obtener_ip_pod "$SUBACCION" "${INPUT[2]}"
            ;;

        add|select)
            if [ "$SUBACCION" == "pod" ] || [ "$SUBACCION" == "pods" ]; then
                PARAMS=("${INPUT[@]:2}")
            else
                PARAMS=("${ARGUMENTOS[@]}")
            fi

            if [ ${#PARAMS[@]} -eq 0 ]; then
                echo "Error: Indica los ID numéricos de los pods. Ejemplo: add 1 10"
            else
                añadir_a_seleccion "${PARAMS[@]}"
            fi
            ;;

        remove|deselect)
            if [ "$SUBACCION" == "pod" ] || [ "$SUBACCION" == "pods" ]; then
                PARAMS=("${INPUT[@]:2}")
            else
                PARAMS=("${ARGUMENTOS[@]}")
            fi

            if [ ${#PARAMS[@]} -eq 0 ]; then
                echo "Error: Indica los ID numéricos de los pods. Ejemplo: remove 1"
            else
                quitar_de_seleccion "${PARAMS[@]}"
            fi
            ;;

        show)
            if [ ${#SELECCIONADOS_PODS[@]} -eq 0 ]; then
                echo "No hay ningún pod seleccionado."
            else
                echo -e "\nPods seleccionados actualmente:"
                for i in "${!SELECCIONADOS_PODS[@]}"; do
                    echo " - ${SELECCIONADOS_PODS[$i]} (namespace: ${SELECCIONADOS_NAMESPACES[$i]})"
                done
                echo ""
            fi
            ;;

        clear-sel)
            SELECCIONADOS_PODS=()
            SELECCIONADOS_NAMESPACES=()
            echo "Selección limpiada."
            ;;

        clear)
            clear
            ;;

        describe)
            if [ ${#SELECCIONADOS_PODS[@]} -eq 0 ]; then
                echo "Error: No hay pods seleccionados."
            else
                for i in "${!SELECCIONADOS_PODS[@]}"; do
                    pod_actual="${SELECCIONADOS_PODS[$i]}"
                    ns_actual="${SELECCIONADOS_NAMESPACES[$i]}"

                    if [ "$SUBACCION" == "-l" ]; then
                        echo -e "\n=== INFORMACIÓN COMPLETA: $pod_actual (NS: $ns_actual) ==="
                        kubectl describe pod "$pod_actual" -n "$ns_actual"
                    else
                        echo -e "\n=== RESUMEN DE POD: $pod_actual ==="
                        echo "Namespace: $ns_actual"
                        kubectl get pod "$pod_actual" -n "$ns_actual" -o custom-columns="ESTADO:.status.phase,IP:.status.podIP,NODO:.spec.nodeName,REINICIOS:.status.containerStatuses[0].restartCount" --no-headers 2>/dev/null | awk '{print "Estado: "$1"\nIP: "$2"\nNodo: "$3"\nReinicios: "$4}'
                        echo -e "\nEventos Recientes:"
                        kubectl get events -n "$ns_actual" --field-selector involvedObject.name="$pod_actual" --no-headers 2>/dev/null | tail -n 3 | awk '{print " - "$0}' || echo " (Sin eventos)"
                        echo "--------------------------------------------------"
                    fi
                done
            fi
            ;;

        logs)
            if [ ${#SELECCIONADOS_PODS[@]} -eq 0 ]; then
                echo "Error: No hay pods seleccionados."
            elif [ ${#SELECCIONADOS_PODS[@]} -gt 1 ]; then
                echo "Error: Selecciona únicamente 1 pod para ver sus logs."
            else
                kubectl logs "${SELECCIONADOS_PODS[0]}" -n "${SELECCIONADOS_NAMESPACES[0]}" --tail=50
            fi
            ;;

        delete)
            if [ ${#SELECCIONADOS_PODS[@]} -eq 0 ]; then
                echo "Error: No hay pods seleccionados para eliminar."
            else
                read -e -p "¿Estás seguro de que deseas eliminar ${#SELECCIONADOS_PODS[@]} pod(s)? (s/n): " confirm
                if [[ "$confirm" =~ ^[sS]$ ]]; then
                    for i in "${!SELECCIONADOS_PODS[@]}"; do
                        kubectl delete pod "${SELECCIONADOS_PODS[$i]}" -n "${SELECCIONADOS_NAMESPACES[$i]}"
                    done
                    SELECCIONADOS_PODS=()
                    SELECCIONADOS_NAMESPACES=()
                    actualizar_pods
                fi
            fi
            ;;

        create)
            if [ -z "$SUBACCION" ]; then
                echo "Error: Indica cuántos pods crear o un rango. Ejemplos: create 5, create 1-10"
            else
                imagen="nginx:alpine"
                if [ "${INPUT[2]}" == "-i" ] || [ "${INPUT[2]}" == "--image" ]; then
                    [ -n "${INPUT[3]}" ] && imagen="${INPUT[3]}"
                fi

                if [[ "$SUBACCION" =~ ^[0-9]+$ ]]; then
                    for ((c=1; c<=SUBACCION; c++)); do
                        kubectl run "pod-app-$c" --image="$imagen" >/dev/null 2>&1
                    done
                    echo "Creados $SUBACCION pods con la imagen '$imagen'."
                elif [[ "$SUBACCION" =~ ^([0-9]+)-([0-9]+)$ ]]; then
                    i_c="${BASH_REMATCH[1]}"
                    f_c="${BASH_REMATCH[2]}"
                    for ((c=i_c; c<=f_c; c++)); do
                        kubectl run "pod-app-$c" --image="$imagen" >/dev/null 2>&1
                    done
                    echo "Creados pods del pod-app-$i_c al pod-app-$f_c con la imagen '$imagen'."
                fi
                actualizar_pods
            fi
            ;;

        test-network)
            probar_red_cluster "$SUBACCION"
            ;;

        test-connections)
            probar_conexion_entre_pods "$SUBACCION" "${INPUT[2]}"
            ;;

        version)
            echo "K3s Manager versión: $VERSION"
            comprobar_actualizacion
            ;;

        update)
            actualizar_k3smanager
            if [ $? -eq 0 ]; then
                echo "Reiniciando el script..."
                export REINICIANDO_K3SMANAGER=true
                exec "$0" "$@"
            fi
            ;;

        help)
            mostrar_ayuda "$SUBACCION"
            ;;

        exit|quit)
            echo "Saliendo de K3s Manager. ¡Hasta luego!"
            exit 0
            ;;

        *)
            echo "Comando no reconocido: '$COMANDO'. Escribe 'help' para ver los comandos disponibles."
            ;;
    esac
done
