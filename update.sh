#!/bin/bash

# Configuración
REPO_DIR="$HOME/Orbis"
EDITOR="nano"

# Función para editar
editar_contenido() {
    $EDITOR "$REPO_DIR/contenido.html"
    git add .
    git commit -m "Actualización: $(date +'%d/%m/%Y %H:%M')"
    git push origin main
    echo "✅ Cambios guardados y publicados"
}

# Menú principal
clear
echo "=== MENÚ DE ACTUALIZACIÓN ==="
echo "1) Editar contenido"
echo "2) Sincronizar cambios"
echo "3) Salir"
echo ""
read -p "Selecciona una opción [1-3]: " opcion

case $opcion in
    1) editar_contenido ;;
    2) git pull origin main ;;
    3) exit 0 ;;
    *) echo "❌ Opción no válida" ;;
esac
