#!/usr/bin/env bash
# Installs KDB-X Community Edition (q) to ~/.kx non-interactively, telemetry off.
# Needs the base64 kc.lic from the KX registration email in KDB_LICENSE_KEY.
set -euo pipefail

if command -v q >/dev/null || [ -x "$HOME/.kx/bin/q" ]; then
  echo "q already installed: $(command -v q || echo "$HOME/.kx/bin/q")"
  exit 0
fi
: "${KDB_LICENSE_KEY:?set KDB_LICENSE_KEY to the base64 kc.lic from KX}"

installer="$(mktemp -d)/install_kdb.sh"
curl -fsSL "https://portal.dl.kx.com/assets/raw/kdb-x/install_kdb/~latest~/install_kdb.sh" -o "$installer"
# The installer echoes the license back; drop any line containing it so it never reaches logs.
TERM="${TERM:-dumb}" bash "$installer" -y --b64lic "$KDB_LICENSE_KEY" 2>&1 | grep -vF "$KDB_LICENSE_KEY" || true
[ -x "$HOME/.kx/bin/q" ] || { echo "KDB-X install failed" >&2; exit 1; }
echo "installed $HOME/.kx/bin/q; open a new shell or: export PATH=\"\$HOME/.kx/bin:\$PATH\""
