#!/bin/bash
REPO_DIR="$HOME/Orbis"
EDITOR="nano"
editar_contenido() {
    $EDITOR "$REPO_DIR/datos.json"
    cd "$REPO_DIR" && git add . && git commit -m "Actualización $(date +'%Y-%m-%d %H:%M')" && git push origin main
    echo "✅ Cambios guardados y publicados"
}
echo "1) Editar contenido"
echo "2) Sincronizar cambios"
echo "3) Salir"
read -p "Selección: " opcion
case $opcion in
    1) editar_contenido ;;
    2) cd "$REPO_DIR" && git pull origin main ;;
    3) exit 0 ;;
    *) echo "Opción no válida" ;;
esac
