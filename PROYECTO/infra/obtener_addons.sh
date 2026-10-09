#!/usr/bin/env sh
# Descarga los módulos OCA en ../addons/oca/ con versiones fijas (no se suben al repo).
# Volver a ejecutarlo actualiza a la versión indicada aquí. Uso: sh obtener_addons.sh
set -e
# En un clon nuevo ../addons no existe (git no guarda carpetas vacías): se crea antes de entrar.
mkdir -p "$(dirname "$0")/../addons/oca"
cd "$(dirname "$0")/../addons"

obtener() {  # repositorio, rama, commit
  destino="oca/$1"
  if [ ! -d "$destino/.git" ]; then
    git clone --quiet --branch "$2" "https://github.com/OCA/$1.git" "$destino"
  fi
  git -C "$destino" fetch --quiet origin "$2"
  git -C "$destino" checkout --quiet "$3"
  echo "$1 -> $(git -C "$destino" log -1 --format='%h %cd' --date=short)"
}

# Gestor documental (dms)
obtener dms 18.0 2d803cc09304e2aebd72881154c425f2104843e8
