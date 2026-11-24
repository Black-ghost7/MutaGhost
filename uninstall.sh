#!/usr/bin/env bash
set -uo pipefail

if [[ -n "${PREFIX:-}" && -d /data/data/com.termux ]]; then
    rm -f "$PREFIX/bin/mutaghost" "$PREFIX/bin/mg"
    echo "[+] MutaGhost removed from Termux."
    exit 0
fi

SUDO=""
[[ $EUID -ne 0 ]] && SUDO="sudo"

$SUDO rm -f /usr/local/bin/mutaghost /usr/local/bin/mg /usr/bin/mutaghost /usr/bin/mg
$SUDO rm -f /usr/share/applications/mutaghost.desktop
$SUDO find /usr/share/icons/hicolor -name mutaghost.png -delete 2>/dev/null || true
command -v gtk-update-icon-cache   >/dev/null 2>&1 && $SUDO gtk-update-icon-cache -f -t /usr/share/icons/hicolor >/dev/null 2>&1 || true
command -v update-desktop-database >/dev/null 2>&1 && $SUDO update-desktop-database /usr/share/applications >/dev/null 2>&1 || true

if [[ $EUID -eq 0 ]]; then TARGET_USER="${SUDO_USER:-}"; else TARGET_USER="$(id -un)"; fi
if [[ -n "$TARGET_USER" ]]; then
    T_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
    DESK="$T_HOME/Desktop"
    if command -v xdg-user-dir >/dev/null 2>&1; then
        d="$(if [[ $EUID -eq 0 ]]; then runuser -u "$TARGET_USER" -- xdg-user-dir DESKTOP 2>/dev/null; else xdg-user-dir DESKTOP 2>/dev/null; fi || true)"
        [[ -n "$d" ]] && DESK="$d"
    fi
    rm -f "$DESK/mutaghost.desktop"
fi
echo "[+] MutaGhost removed."
