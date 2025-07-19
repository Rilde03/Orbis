#!/bin/bash

# Configuración
REPO_DIR="$HOME/Orbis"
GIT_REPO="https://github.com/Rilde03/Orbis.git"

# Ir al directorio del repositorio
cd "$REPO_DIR" || exit

# Actualizar desde GitHub
git pull origin main

# Hacer commit de cualquier cambio local
git add .
git commit -m "Actualización automática desde Termux - $(date +'%Y-%m-%d %H:%M:%S')"

# Subir cambios
git push origin main

echo "✅ Actualización completada - $(date +'%Y-%m-%d %H:%M:%S')"
