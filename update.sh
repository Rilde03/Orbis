#!/bin/bash

REPO_DIR="$HOME/Orbis"
EDITOR="nano"

function edit_content() {
    echo "Editando el archivo de contenido..."
    $EDITOR "$REPO_DIR/datos.json"
    
    echo -n "¿Quieres subir los cambios a GitHub? [s/n]: "
    read respuesta
    
    if [[ "$respuesta" =~ ^[SsYy] ]]; then
        cd "$REPO_DIR"
        git add datos.json
        git commit -m "Actualización de contenido - $(date +'%d/%m/%Y %H:%M')"
        git push origin main
        echo "✅ Cambios subidos correctamente"
    else
        echo "❌ Cambios no subidos"
    fi
}

while true; do
    clear
    echo "=== MENÚ DE ACTUALIZACIÓN ==="
    echo ""
    echo "1) Editar contenido de bienvenidas"
    echo "2) Sincronizar desde GitHub"
    echo "3) Salir"
    echo ""
    read -p "Selecciona una opción [1-3]: " opcion
    
    case $opcion in
        1) edit_content ;;
        2) cd "$REPO_DIR" && git pull origin main
           echo "✅ Sincronización completada"
           sleep 1 ;;
        3) exit 0 ;;
        *) echo "❌ Opción no válida"
           sleep 1 ;;
    esac
done
