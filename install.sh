#!/usr/bin/env bash
# MutaGhost installer. The tool itself needs no root to run; this script only
# needs root to copy files into system-wide locations (skip that on Termux).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- Termux (Android, no root, no desktop icon) --------------------------
if [[ -n "${PREFIX:-}" && -d /data/data/com.termux ]]; then
    echo "[*] Termux detected"
    pkg update -y
    pkg install -y python
    install -m 0755 "$SCRIPT_DIR/mutaghost.py" "$PREFIX/bin/mutaghost"
    ln -sf "$PREFIX/bin/mutaghost" "$PREFIX/bin/mg"
    echo "[+] Done. Start with: mutaghost   (or: mg)"
    exit 0
fi

# ---- Linux desktop ---------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    SUDO="sudo"
    command -v sudo >/dev/null 2>&1 || { echo "[-] Run as root, or install sudo."; exit 1; }
else
    SUDO=""
fi

if command -v apt-get >/dev/null 2>&1; then
    echo "[*] Debian-based system (Kali, Ubuntu, Debian, Mint, Zorin...)"
    $SUDO apt-get update -qq
    $SUDO apt-get install -y python3
elif command -v dnf >/dev/null 2>&1; then
    echo "[*] Fedora / RHEL-based system"
    $SUDO dnf install -y python3
elif command -v pacman >/dev/null 2>&1; then
    echo "[*] Arch-based system"
    $SUDO pacman -S --noconfirm --needed python
elif command -v zypper >/dev/null 2>&1; then
    echo "[*] openSUSE"
    $SUDO zypper --non-interactive install python3
else
    echo "[!] Unrecognized package manager. Make sure Python 3.8+ is installed, then continuing..."
fi

echo "[*] Installing MutaGhost to /usr/local/bin"
$SUDO install -m 0755 "$SCRIPT_DIR/mutaghost.py" /usr/local/bin/mutaghost
$SUDO ln -sf /usr/local/bin/mutaghost /usr/local/bin/mg

# Some systems (e.g. current Kali) do not keep /usr/local/bin in sudo's PATH.
if command -v sudo >/dev/null 2>&1 && ! sudo sh -c 'command -v mutaghost' >/dev/null 2>&1; then
    $SUDO ln -sf /usr/local/bin/mutaghost /usr/bin/mutaghost
    $SUDO ln -sf /usr/local/bin/mg /usr/bin/mg
fi

# ---- Icon and application-menu entry --------------------------------------
if [[ -d "$SCRIPT_DIR/icons/hicolor" && -f "$SCRIPT_DIR/mutaghost.desktop" ]]; then
    echo "[*] Installing icon and application-menu entry..."
    while IFS= read -r f; do
        rel="${f#"$SCRIPT_DIR"/icons/hicolor/}"
        $SUDO install -D -m 644 "$f" "/usr/share/icons/hicolor/$rel"
    done < <(find "$SCRIPT_DIR/icons/hicolor" -type f -name '*.png')
    $SUDO install -D -m 644 "$SCRIPT_DIR/mutaghost.desktop" /usr/share/applications/mutaghost.desktop
    command -v gtk-update-icon-cache   >/dev/null 2>&1 && $SUDO gtk-update-icon-cache -f -t /usr/share/icons/hicolor >/dev/null 2>&1 || true
    command -v update-desktop-database >/dev/null 2>&1 && $SUDO update-desktop-database /usr/share/applications >/dev/null 2>&1 || true

    if [[ $EUID -eq 0 ]]; then TARGET_USER="${SUDO_USER:-}"; else TARGET_USER="$(id -un)"; fi
    if [[ -n "$TARGET_USER" ]]; then
        as_user() { if [[ $EUID -eq 0 ]]; then runuser -u "$TARGET_USER" -- "$@"; else "$@"; fi; }
        T_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
        DESK="$(as_user xdg-user-dir DESKTOP 2>/dev/null || true)"
        { [[ -n "$DESK" ]] && [[ -d "$DESK" ]]; } || DESK="$T_HOME/Desktop"
        if [[ -d "$DESK" ]]; then
            SHORTCUT="$DESK/mutaghost.desktop"
            as_user cp /usr/share/applications/mutaghost.desktop "$SHORTCUT"
            as_user chmod +x "$SHORTCUT"
            as_user gio set "$SHORTCUT" metadata::trusted true >/dev/null 2>&1 || true
            echo "[+] Desktop shortcut: $SHORTCUT"
            echo "    (if it shows a warning icon: right-click -> Allow Launching)"
        fi
    fi
fi

cat << 'BANNER'

+----------------------------------------------------------+
|  MutaGhost installed successfully                        |
|                                                            |
|  Click the MutaGhost icon in the applications menu,      |
|  or just type:                                            |
|    mutaghost            # interactive menu                |
|    mg                   # same, shorter                   |
|    mutaghost -w admin -cpa -o out.txt   # one-shot run     |
|    mutaghost --help     # all options                     |
+----------------------------------------------------------+
BANNER
