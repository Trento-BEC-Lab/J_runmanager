#!/usr/bin/env bash
# Remove the terminal command and application-menu launcher.
set -euo pipefail

COMMAND="$HOME/.local/bin/JRunmanager"
APPLICATIONS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_FILE="$APPLICATIONS_DIR/JRunmanager.desktop"

if [[ -e "$COMMAND" && ! -L "$COMMAND" ]]; then
    printf 'Refusing to remove an existing non-symlink: %s\n' "$COMMAND" >&2
    exit 1
fi

rm -f -- "$COMMAND" "$DESKTOP_FILE"

if [[ -d "$APPLICATIONS_DIR" ]] && command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR"
fi

printf 'Removed %s\nRemoved %s\n' "$COMMAND" "$DESKTOP_FILE"
