#!/bin/bash

# Configuración
REPO_DIR="$HOME/Orbis"
EDITOR="nano"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Función para editar
editar_contenido() {
    echo -e "${GREEN}Editando contenido...${NC}"
    $EDITOR "$REPO_DIR/contenido.html"
    
    echo -e "${GREEN}Subiendo cambios a GitHub...${NC}"
    cd "$REPO_DIR" && git add . && git commit -m "Actualización: $(date +'%d/%m/%Y %H:%M')" && git push origin main
    
    echo -e "${GREEN}✅ Cambios guardados y publicados${NC}"
}

# Menú principal
while true; do
    clear
    echo -e "=== ${GREEN}ACTUALIZADOR DE CONTENIDO${NC} ==="
    echo -e "${GREEN}1)${NC} Editar contenido"
    echo -e "${GREEN}2)${NC} Sincronizar desde GitHub"
    echo -e "${RED}3)${NC} Salir"
    echo ""
    read -p "Selecciona una opción [1-3]: " opcion

    case $opcion in
        1) editar_contenido ;;
        2) git pull origin main
           echo -e "${GREEN}✅ Sincronización completada${NC}"
           sleep 1 ;;
        3) exit 0 ;;
        *) echo -e "${RED}❌ Opción no válida${NC}"
           sleep 1 ;;
    esac
done
