#!/usr/bin/env bash
# Install the terminal command and application-menu launcher for this checkout.
set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
BIN_DIR="$HOME/.local/bin"
APPLICATIONS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
COMMAND="$BIN_DIR/JRunmanager"
DESKTOP_FILE="$APPLICATIONS_DIR/JRunmanager.desktop"

if [[ -e "$COMMAND" && ! -L "$COMMAND" ]]; then
    printf 'Refusing to replace an existing non-symlink: %s\n' "$COMMAND" >&2
    exit 1
fi

mkdir -p "$BIN_DIR" "$APPLICATIONS_DIR"
ln -sfn "$SCRIPT_DIR/JRunmanager" "$COMMAND"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=JRunmanager
Comment=Launch editable runmanager in labscript_test_v1
Exec="$COMMAND"
Icon=$REPO_DIR/runmanager/runmanager.svg
Terminal=true
Categories=Science;Development;
StartupNotify=true
StartupWMClass=runmanager-labscript_test_v1
EOF

if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "$DESKTOP_FILE"
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR"
fi

printf 'Installed %s\nInstalled %s\n' "$COMMAND" "$DESKTOP_FILE"
