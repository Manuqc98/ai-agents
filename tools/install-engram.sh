#!/usr/bin/env bash
# tools/install-engram.sh — Instalador automático y agnóstico de Engram
# Descarga el binario oficial compilado de GitHub Releases (Gentleman-Programming/engram)
# sin necesidad de tener instalado el compilador de Go.

set -euo pipefail

DEST_DIR="${HOME}/.local/bin"
mkdir -p "${DEST_DIR}"

# Detectar Sistema Operativo y Arquitectura
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "${ARCH}" in
  x86_64|amd64)
    ARCH="amd64"
    ;;
  aarch64|arm64)
    ARCH="arm64"
    ;;
  *)
    echo "Error: Arquitectura no soportada (${ARCH})" >&2
    exit 1
    ;;
esac

case "${OS}" in
  linux)
    OS="linux"
    ;;
  darwin)
    OS="darwin"
    ;;
  *)
    echo "Error: Sistema operativo no soportado (${OS})" >&2
    exit 1
    ;;
esac

# Obtener la última versión disponible vía GitHub API o usar fallback v3.6.0
VERSION=""
if command -v gh >/dev/null 2>&1; then
  VERSION="$(gh release view --repo Gentleman-Programming/engram --json tagName -q .tagName 2>/dev/null || true)"
fi
if [ -z "${VERSION}" ]; then
  VERSION="v3.6.0"
fi

VERSION_NUM="${VERSION#v}"
TARBALL="engram_${VERSION_NUM}_${OS}_${ARCH}.tar.gz"
URL="https://github.com/Gentleman-Programming/engram/releases/download/${VERSION}/${TARBALL}"

echo "==> Descargando Engram ${VERSION} (${OS}_${ARCH})..."
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

curl -fsSL "${URL}" -o "${TMP_DIR}/${TARBALL}"
tar -xzf "${TMP_DIR}/${TARBALL}" -C "${TMP_DIR}"

# Localizar el binario desempaquetado e instalarlo
if [ -f "${TMP_DIR}/engram" ]; then
  install -m 755 "${TMP_DIR}/engram" "${DEST_DIR}/engram"
elif [ -f "${TMP_DIR}/bin/engram" ]; then
  install -m 755 "${TMP_DIR}/bin/engram" "${DEST_DIR}/engram"
else
  # Si el tarball contiene otra estructura, buscar el ejecutable
  BIN_PATH="$(find "${TMP_DIR}" -type f -name "engram" | head -n 1)"
  if [ -n "${BIN_PATH}" ]; then
    install -m 755 "${BIN_PATH}" "${DEST_DIR}/engram"
  else
    echo "Error: no se encontró el binario engram en el paquete descargado" >&2
    exit 1
  fi
fi

echo "✓ Engram instalado correctamente en: ${DEST_DIR}/engram"

# Comprobar PATH
if ! echo "${PATH}" | tr ':' '\n' | grep -qx "${DEST_DIR}"; then
  echo "Aviso: ${DEST_DIR} no está en tu PATH actual."
  echo "Añádelo a tu ~/.bashrc o ~/.zshrc con:"
  echo "  export PATH=\"\${HOME}/.local/bin:\${PATH}\""
fi

"${DEST_DIR}/engram" --version || true
