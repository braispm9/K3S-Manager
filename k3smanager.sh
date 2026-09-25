#!/bin/bash

if [ "$REINICIANDO_K3SMANAGER" = true ]; then
    unset REINICIANDO_K3SMANAGER
fi
export PROMPT="k3s> "
# --- FUNCIONES DE AYUDA Y CONSOLA INTERACTIVA ---

mostrar_ayuda() {
    local cmd="$1"

    if [ -z "$cmd" ]; then
        echo -e "\nComandos disponibles para Pods:"
        echo "  pods [namespace|-A]        - Listar pods con su ID numérico (-A para todos)"
        echo "  add pod <IDs...>           - Añadir pod(s) a la selección activa (ej: add pod 1 2)"
        echo "  remove pod <IDs...>        - Quitar pod(s) de la selección activa (ej: remove pod 1)"
        echo "  clear-sel                  - Limpiar toda la selección de pods actual"
        echo "  clear                      - Limpiar la pantalla de la terminal"
        echo "  show                       - Mostrar pods seleccionados actualmente"
        echo ""
        echo "Comandos de información y acción:"
        echo "  describe [-l]              - Ver información resumida o completa (-l) de la selección"
        echo "  logs                       - Mostrar logs (requiere seleccionar solo 1 pod)"
        echo "  delete                     - Eliminar el/los pod(s) seleccionados"
        echo "  create <nombre> <imagen>   - Crea un pod con nombre e imagen proporcionados"
        echo ""
        echo "Pruebas de Red y Diagnóstico:"
        echo "  test-network [rango|-a]    - Probar conectividad global (-a o --all para todas)"
        echo "  test-connections [orig dest] - Probar tráfico directo entre dos pods"
        echo ""
        echo "  version                       - Verifica si es la última versión y muestra la versión actual"
        echo "  update                        - Instala la ultima version del software y se reactiva"
        echo "  help [comando]             - Ayuda general o de una función específica"
        echo -e "  exit | quit                - Salir de la consola\n"
        return
    fi

    case $cmd in
        pods|list)
            echo -e "\nUSO: pods [namespace|-A]"
            echo "Muestra todos los pods disponibles asignándoles un ID numérico."
            echo ""
            ;;
        describe)
            echo -e "\nUSO: describe [-l]"
            echo "Muestra la información de los pods seleccionados."
            echo "  describe     -> Vista resumida (Estado, IP, Nodo, Restarts, Eventos)."
            echo "  describe -l  -> Vista completa detallada (kubectl describe)."
            echo ""
            ;;
        test-network)
            echo -e "\nUSO: test-network [número | -a | --all]"
            echo "Prueba la conexión desde un pod de prueba hacia las máquinas nginx-prueba."
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

    # Detectar la ruta del script local
    if [ -n "$ZSH_VERSION" ]; then
        SCRIPT_ACTUAL="${(%):-%x}"
    else
        SCRIPT_ACTUAL="${BASH_SOURCE[0]:-$0}"
    fi
    RUTA_LOCAL="$(readlink -f "$SCRIPT_ACTUAL" 2>/dev/null || realpath "$SCRIPT_ACTUAL" 2>/dev/null || echo "$SCRIPT_ACTUAL")"

    # Descargar la versión remota a un archivo temporal
    TEMP_REMOTE=$(mktemp)
    RAW_URL="https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/${SCRIPT_NAME}?t=$(date +%s)"

    if curl -fsSL -H "Cache-Control: no-cache" -o "$TEMP_REMOTE" "$RAW_URL"; then
        # Obtener el hash de ambos archivos
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
    
    # URL de la API oficial para evitar la caché de CDN Fastly/GitHub Raw
    API_URL="https://api.github.com/repos/${GITHUB_USER}/${REPO_NAME}/contents/${SCRIPT_NAME}?ref=${BRANCH}"

    # Detectar la ruta real del script en ejecución
    if [ -n "$ZSH_VERSION" ]; then
        ORIGEN="${(%):-%x}"
    else
        ORIGEN="${BASH_SOURCE[0]:-$0}"
    fi

    RUTA_DESTINO="$(readlink -f "$ORIGEN" 2>/dev/null || realpath "$ORIGEN" 2>/dev/null || echo "$ORIGEN")"
    TEMP_FILE=$(mktemp)
    
    # Petición a la API usando la cabecera 'application/vnd.github.v3.raw'
    if curl -fsSL -H "Accept: application/vnd.github.v3.raw" -H "Cache-Control: no-cache" -o "$TEMP_FILE" "$API_URL"; then
        if [ -s "$TEMP_FILE" ]; then
            mv "$TEMP_FILE" "$RUTA_DESTINO"
            chmod +x "$RUTA_DESTINO"
            echo "   [OK] Versión en tiempo real descargada correctamente."
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

    while read -r ns name; do
        if [ -n "$name" ]; then
            PODS_NS_LIST+=("$ns")
            PODS_LIST+=("$name")
        fi
    done < <(kubectl get pods $ns_flag --no-headers -o custom-columns="NS:.metadata.namespace,NAME:.metadata.name" 2>/dev/null)
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
            echo "Error: El ID '$id' no es válido. Ejecuta 'pods' primero."
            return 1
        fi
    done
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
                echo "Pod '$pod' (namespace: $ns) añadido a la selección."
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

# --- FUNCIONES DE EVALUACIÓN Y CONEXIONES DE RED ---

probar_red_cluster() {
    local arg="$1"
    local total_maquinas=0

    if [ "$arg" == "-a" ] || [ "$arg" == "--all" ] || [ -z "$arg" ]; then
        total_maquinas=$(kubectl get pods --all-namespaces --no-headers | grep -c "nginx-prueba" 2>/dev/null)
        if [ "$total_maquinas" -eq 0 ]; then
            total_maquinas=50
        fi
    elif [[ "$arg" =~ ^[0-9]+$ ]]; then
        total_maquinas=$arg
    else
        echo "Opción no reconocida para test-network. Usa un número, -a o --all."
        return 1
    fi

    echo "Lanzando contenedor de pruebas..."
    kubectl run probador-red --image=curlimages/curl --restart=Never -- sleep 3600 >/dev/null 2>&1
    kubectl wait --for=condition=Ready pod/probador-red --timeout=10s >/dev/null 2>&1

    echo -e "\nProbando comunicación con las $total_maquinas máquinas...\n"
    ERRORES=0
    rm -f conexion.log >/dev/null 2>&1

    for ((i=1; i<=total_maquinas; i++)); do
        STATUS=$(kubectl exec probador-red -- curl -s -o /dev/null -w "%{http_code}" "http://nginx-prueba-$i" 2>/dev/null)

        if [[ ! "$STATUS" =~ ^[0-9]+$ ]] || [ "$STATUS" -ne 200 ]; then
            echo "[X] Máquina $i Error de conexión (HTTP ${STATUS:-SIN RESPUESTA})" >> conexion.log
            ERRORES=$((ERRORES + 1))
        fi
    done

    if [ $ERRORES -gt 0 ]; then
        echo -e "[X] Se encontraron $ERRORES errores de conexión."
        echo "Verifica el archivo conexion.log para detalles."
    else
        echo -e "[OK] ¡Comunicaciones exitosas con las $total_maquinas máquinas!\n"

        read -e -p "¿Deseas cargar automáticamente estos pods en la selección? (s/n): " opcion
        if [[ "$opcion" =~ ^[sS]$ ]]; then
            actualizar_pods "-A"
            for idx in "${!PODS_LIST[@]}"; do
                if [[ "${PODS_LIST[$idx]}" =~ nginx-prueba- ]]; then
                    añadir_a_seleccion "$((idx + 1))" >/dev/null
                fi
            done
            echo "Pods importados a la selección activa."
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

        # 1. Obtener la IP interna del pod destino
        local ip_destino=$(kubectl get pod "$pod_destino" -n "$ns_destino" -o jsonpath='{.status.podIP}' 2>/dev/null)

        if [ -z "$ip_destino" ]; then
            echo "Error: No se pudo obtener la IP del pod destino '$pod_destino'."
            return 1
        fi

        echo -e "\nProbando conectividad desde '$pod_origen' hacia '$pod_destino' ($ip_destino)..."

        # 2. Intentar prueba con wget o curl (por si alguno no está instalado en el pod de origen)
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

# --- BUCLE PRINCIPAL (TERMINAL INTERACTIVA) ---

echo "=================================================="
echo " Consola Interactiva K3s (Gestión de Pods)"
echo " Escribe 'help' o 'help <comando>' para asistencia."
echo "=================================================="

actualizar_pods "-A"

while true; do

    PROMPT="${PROMPT:-k3s> }"
    
    read -r -p "k3s> " ENTRADA_RAW
    # Si se presiona Enter sin escribir nada, continua
    if [ -z "$ENTRADA_RAW" ]; then
        continue
    fi

    # Convertimos la cadena de texto en un array de palabras
    read -a INPUT <<< "$ENTRADA_RAW"

    ACCION=${INPUT[0]}
    SUBACCION=${INPUT[1]}
    ARGUMENTOS=("${INPUT[@]:1}")

    case $ACCION in
        list)
            FLAG="-A"
            if [ -n "$SUBACCION" ] && [ "$SUBACCION" != "pod" ] && [ "$SUBACCION" != "pods" ]; then
                FLAG="-n $SUBACCION"
            fi
            actualizar_pods "$FLAG"

            if [ ${#PODS_LIST[@]} -eq 0 ]; then
                echo "No se encontraron pods."
            else
                echo -e "\nID   NAMESPACE         NOMBRE DEL POD"
                echo "--------------------------------------------------"
                for i in "${!PODS_LIST[@]}"; do
                    printf "%-4d %-17s %s\n" $((i + 1)) "${PODS_NS_LIST[$i]}" "${PODS_LIST[$i]}"
                done
                echo ""
            fi
            ;;

        select)
            if [ "$SUBACCION" == "pod" ] || [ "$SUBACCION" == "pods" ]; then
                PARAMS=("${INPUT[@]:2}")
            else
                PARAMS=("${ARGUMENTOS[@]}")
            fi

            if [ ${#PARAMS[@]} -eq 0 ]; then
                echo "Error: Indica los ID numéricos de los pods. Ejemplo: add 1 2"
            else
                añadir_a_seleccion "${PARAMS[@]}"
            fi
            ;;

        deselect)
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

        test-network)
            probar_red_cluster "$SUBACCION"
            ;;

        test-connections)
            probar_conexion_entre_pods "$SUBACCION" "${INPUT[2]}"
            ;;

        help)
            mostrar_ayuda "$SUBACCION"
            ;;

        exit)
            echo "Saliendo de la consola K3s..."
            break
            ;;

        update)
            if actualizar_k3smanager; then
                echo -e "\n  [OK] Reemplazando sesión con la nueva versión..."
                sleep 1
                
                # Restaurar explícitamente el prompt
                export PROMPT="k3s> "
                
                # Reejecutar la shell limpiamente cargando el archivo actualizado
                exec "$SHELL" -c "source '$RUTA_DESTINO' 2>/dev/null || source '$RUTA_ABSOLUTA'"
            fi
            ;;
            
        create)
            NOMBRE_POD=${INPUT[1]}
            IMAGEN_POD=${INPUT[2]}

            if [ -z "$NOMBRE_POD" ] || [ -z "$IMAGEN_POD" ]; then
                echo "Uso: create <nombre_pod> <imagen>"
                echo "Ejemplo: create nginx-test nginx:latest"
            else
                echo "Creando pod '$NOMBRE_POD' con la imagen '$IMAGEN_POD'..."
                kubectl run "$NOMBRE_POD" --image="$IMAGEN_POD"
            fi
            ;;
            
        version)
            echo "Esta es la versión 1.3.3"
            comprobar_actualizacion
            ;;
        
        *)
            echo "Comando no reconocido: '$ACCION'. Escribe 'help' para ayuda."
            ;;
    esac
done
}
