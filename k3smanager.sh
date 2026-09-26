#!/bin/bash
VERSION="Release 2.3"
if [ "$REINICIANDO_K3SMANAGER" = true ]; then
    unset REINICIANDO_K3SMANAGER
fi
export PROMPT="k3s> "

# --- FUNCIONES DE AYUDA Y CONSOLA INTERACTIVA ---

mostrar_ayuda() {
    local cmd="$1"

    if [ -z "$cmd" ]; then
        echo -e "\nComandos disponibles para Pods:"
        echo "  pods [namespace|-A]        - Listar pods excluyendo kube-system con su ID numérico"
        echo "  add pod <IDs...>           - Añadir pod(s) a la selección activa (ej: add pod 1 10)"
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
        echo "Pruebas de Red y Diagnóstico:"
        echo "  test-network [N | N-M |-a] - Crear y probar conectividad hacia pods específicos o todos"
        echo "  test-connections [orig dest] - Probar tráfico directo entre dos pods"
        echo ""
        echo "  version                    - Verifica si es la última versión y muestra la versión actual"
        echo "  update                     - Instala la última versión del software y se reactiva"
        echo "  help [comando]             - Ayuda general o de una función específica"
        echo -e "  exit | quit                - Salir de la consola\n"
        return
    fi

    case $cmd in
        pods|list)
            echo -e "\nUSO: pods [namespace|-A]"
            echo "Muestra los pods disponibles (ignorando el namespace kube-system) asignando IDs ordenados."
            echo ""
            ;;
        ip)
            echo -e "\nUSO: ip <ID_numérico | nombre_pod> [namespace]"
            echo "Muestra la dirección IP interna asignada al pod en el clúster."
            echo "Ejemplos:"
            echo "  ip 3"
            echo "  ip pod-prueba-1"
            echo "  ip \"pod-prueba-1\" default"
            echo ""
            ;;
        create)
            echo -e "\nUSO: create <N | N-M> [--image <imagen> | -i <imagen>]"
            echo "Crea pods de prueba individuales o por rango. Si no se especifica imagen, usa 'nginx:alpine'."
            echo "Ejemplos:"
            echo "  create 1                            -> Crea pod-prueba-1 con nginx:alpine"
            echo "  create 1-50                         -> Crea de pod-prueba-1 a 50 con nginx:alpine"
            echo "  create 5 --image redis:alpine       -> Crea pod-prueba-5 con redis:alpine"
            echo "  create 1-10 -i ubuntu               -> Crea de pod-prueba-1 a 10 con ubuntu"
            echo ""
            ;;
        describe)
            echo -e "\nUSO: describe [-l]"
            echo "Muestra la información de los pods seleccionados."
            echo "  describe   -> Vista resumida (Estado, IP, Nodo, Restarts, Eventos)."
            echo "  describe -l  -> Vista completa detallada (kubectl describe)."
            echo ""
            ;;
        test-network)
            echo -e "\nUSO: test-network [N | N-M | -a | --all]"
            echo "Crea automáticamente los pods del rango especificado si no existen y mide su conectividad."
            echo "Ejemplos:"
            echo "  test-network 1-2    -> Crea y prueba solo pod-prueba-1 y pod-prueba-2"
            echo "  test-network 5      -> Crea y prueba solo hasta pod-prueba-5"
            echo "  test-network -a     -> Prueba todos los 50 pods"
            echo ""
            ;;
        test-connections)
            echo -e "\nUSO: test-connections [ID_ORIGEN] [ID_DESTINO]"
            echo "Realiza una petición HTTP (curl) directa entre dos pods especificados por su ID."
            echo ""
            ;;
        clear)
            echo -e "\nUSO: clear"
            echo "Limpia la pantalla de la terminal."
            echo ""
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
            echo "  [OK] Estás utilizando la última versión disponible."
        else
            echo "  [!] Hay una nueva versión disponible en GitHub."
            echo "      Ejecuta 'update' para actualizar el script."
        fi
    else
        rm -f "$TEMP_REMOTE"
        echo "  [X] No se pudo conectar con GitHub para verificar la versión."
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
    local ns_flag="${1:---all-namespaces}"
    PODS_LIST=()
    PODS_NS_LIST=()

    # Ordenación natural (-V) ignorando el namespace kube-system
    while read -r ns name; do
        if [ -n "$name" ] && [ "$ns" != "kube-system" ]; then
            PODS_NS_LIST+=("$ns")
            PODS_LIST+=("$name")
        fi
    done < <(kubectl get pods $ns_flag --no-headers -o custom-columns="NS:.metadata.namespace,NAME:.metadata.name" 2>/dev/null | sort -k2 -V)
}

obtener_pods_por_indice() {
    local ids=("$@")
    PODS_TEMPORALES=()
    NS_TEMPORALES=()

    for id in "${ids[@]}"; do
        if [[ "$id" =~ ^[0-9]+$ ]] && [ "$id" -ge 1 ] && [ "$id" -le "${#PODS_LIST[@]}" ]; then
            idx=$((id - 1))
            PODS_TEMPORALES+=("${PODS_LIST[$idx]}")
            NS_TEMPORALES+=("${PODS_NS_LIST[$idx]}")
        else
            echo "Error: El ID '$id' no es válido. Ejecuta 'pods' para refrescar la lista."
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

    actualizar_pods "-A"

    local pod_nombre=""
    local pod_ns=""

    if [[ "$target" =~ ^[0-9]+$ ]]; then
        if [ "$target" -ge 1 ] && [ "$target" -le "${#PODS_LIST[@]}" ]; then
            local idx=$((target - 1))
            pod_nombre="${PODS_LIST[$idx]}"
            pod_ns="${PODS_NS_LIST[$idx]}"
        else
            echo "Error: El ID '$target' no existe. Ejecuta 'pods' para ver la lista activa."
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
        echo "Error: No se encontró el pod '$pod_nombre' en ningún namespace."
        return 1
    fi

    local ip=$(kubectl get pod "$pod_nombre" -n "$pod_ns" -o jsonpath='{.status.podIP}' 2>/dev/null)
    local status=$(kubectl get pod "$pod_nombre" -n "$pod_ns" -o jsonpath='{.status.phase}' 2>/dev/null)

    if [ -n "$ip" ]; then
        echo -e "IP de '$pod_nombre' (NS: \033[1;34m${pod_ns}\033[0m | Estado: \033[1;33m${status}\033[0m): \033[1;32m$ip\033[0m"
    else
        echo "Error: El pod '$pod_nombre' existe en '$pod_ns' (Estado: ${status:-Desconocido}), pero aún no tiene IP asignada."
        return 1
    fi
}

añadir_a_seleccion() {
    actualizar_pods "-A"
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
                echo "Pod '$pod' (namespace: $ns) añadido a la selección."
            else
                echo "El pod '$pod' ya estaba seleccionado."
            fi
        done
    fi
}

quitar_de_seleccion() {
    actualizar_pods "-A"
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
        if ! kubectl get pod "pod-prueba-$i" >/dev/null 2>&1; then
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
        IP_POD=$(kubectl get pod "pod-prueba-$i" -o jsonpath='{.status.podIP}' 2>/dev/null)

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
            actualizar_pods "-A"
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

    actualizar_pods "-A"

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

        echo -e "\nProbando conectividad desde '$pod_origen' hacia '$pod_destino' ($ip_destino)..."

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

actualizar_pods "-A"

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
            FLAG="-A"
            if [ -n "$SUBACCION" ] && [ "$SUBACCION" != "pod" ] && [ "$SUBACCION" != "pods" ] && [ "$SUBACCION" != "-A" ]; then
                FLAG="-n $SUBACCION"
            fi
            actualizar_pods "$FLAG"

            if [ ${#PODS_LIST[@]} -eq 0 ]; then
                echo "No se encontraron pods de aplicación/prueba disponibles."
            else
                echo -e "\nID   NAMESPACE         NOMBRE DEL POD"
                echo "--------------------------------------------------"
                for i in "${!PODS_LIST[@]}"; do
                    printf "%-4d %-17s %s\n" $((i + 1)) "${PODS_NS_LIST[$i]}" "${PODS_LIST[$i]}"
                done
                echo ""
            fi
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
                echo "Error: Selecciona solo 1 pod para ver sus logs."
            else
                kubectl logs "${SELECCIONADOS_PODS[0]}" -n "${SELECCIONADOS_NAMESPACES[0]}"
            fi
            ;;

        delete)
            if [ ${#SELECCIONADOS_PODS[@]} -eq 0 ]; then
                echo "Error: No hay pods seleccionados."
            else
                for i in "${!SELECCIONADOS_PODS[@]}"; do
                    echo "Eliminando pod '${SELECCIONADOS_PODS[$i]}'..."
                    kubectl delete pod "${SELECCIONADOS_PODS[$i]}" -n "${SELECCIONADOS_NAMESPACES[$i]}"
                done
                SELECCIONADOS_PODS=()
                SELECCIONADOS_NAMESPACES=()
            fi
            ;;

        create)
            PARAM="${INPUT[1]}"
            IMAGEN_POD="nginx:alpine"
            INICIO=0
            FIN=0

            for ((j=1; j<${#INPUT[@]}; j++)); do
                if [ "${INPUT[$j]}" == "--image" ] || [ "${INPUT[$j]}" == "-i" ]; then
                    SIG_IDX=$((j + 1))
                    if [ -n "${INPUT[$SIG_IDX]}" ]; then
                        IMAGEN_POD="${INPUT[$SIG_IDX]}"
                    fi
                    break
                fi
            done

            if [[ "$PARAM" =~ ^[0-9]+$ ]]; then
                INICIO=$PARAM
                FIN=$PARAM
            elif [[ "$PARAM" =~ ^([0-9]+)-([0-9]+)$ ]]; then
                INICIO="${BASH_REMATCH[1]}"
                FIN="${BASH_REMATCH[2]}"
            fi

            if [ "$INICIO" -ge 1 ] && [ "$FIN" -le 50 ] && [ "$INICIO" -le "$FIN" ]; then
                if [ "$INICIO" -eq "$FIN" ]; then
                    echo "Creando pod-prueba-$INICIO con la imagen '$IMAGEN_POD'..."
                else
                    echo "Creando pods de prueba del $INICIO al $FIN con la imagen '$IMAGEN_POD'..."
                fi

                for ((i=INICIO; i<=FIN; i++)); do
                    if ! kubectl get pod "pod-prueba-$i" >/dev/null 2>&1; then
                        kubectl run "pod-prueba-$i" --image="$IMAGEN_POD" >/dev/null 2>&1
                        echo "Pod 'pod-prueba-$i' creado ($IMAGEN_POD)."
                    else
                        echo "Pod 'pod-prueba-$i' ya existe."
                    fi
                done
                actualizar_pods "-A"
            else
                echo "Error: Especifica un pod (1-50) o un rango válido (ej: 1-50, 5-10)."
                echo "Ejemplos:"
                echo "  create 1"
                echo "  create 1-50"
                echo "  create 1 --image redis:alpine"
                echo "  create 1-10 -i ubuntu"
            fi
            ;;

        test-network)
            probar_red_cluster "$SUBACCION"
            ;;

        test-connections)
            probar_conexion_entre_pods "$SUBACCION" "${INPUT[2]}"
            ;;

        help)
            mostrar_ayuda "$SUBACCION"
            ;;

        exit|quit)
            echo "Saliendo de la consola K3s..."
            break
            ;;

        update)
            if actualizar_k3smanager; then
                echo -e "\nRecargando K3s Manager...\n"
                sleep 1

                export PROMPT="k3s> "

                if [ -n "$RUTA_DESTINO" ] && [ -f "$RUTA_DESTINO" ]; then
                    source "$RUTA_DESTINO"
                fi

                break
            fi
            ;;

        version)
            echo "Esta es la versión: $VERSION"
            comprobar_actualizacion
            ;;

        *)
            echo "Comando no reconocido: '$COMANDO'. Escribe 'help' para ayuda."
            ;;
    esac
done
