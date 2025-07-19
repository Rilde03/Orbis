#!/data/data/com.termux/files/usr/bin/bash

# Configuración
REPO_DIR="$HOME/Orbis"
GITHUB_USER="Rilde03"
GITHUB_REPO="Orbis"
GITHUB_BRANCH="main"
COMMIT_MSG="Actualización automática desde Termux"

# Actualizar contenido
cd $REPO_DIR

# Agregar todos los cambios
git add -A

# Hacer commit
git commit -m "$COMMIT_MSG"

# Subir cambios
git push https://${GITHUB_USER}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git ${GITHUB_BRANCH}

echo "Contenido actualizado correctamente en GitHub Pages"
