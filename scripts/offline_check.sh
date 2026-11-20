#!/usr/bin/env bash
# Prove the demo is offline (for the video): shows radios/links, routes and a failing ping.
#   scripts/offline_check.sh             # report only
#   scripts/offline_check.sh --go-offline # turn Wi-Fi off first; unplug any LAN cable by hand
# Ethernet devices are not touched: the USB-C link to the laptop (usb0/usb1/l4tbr0) also shows up as ethernet.
set -uo pipefail
if [ "${1:-}" = "--go-offline" ]; then
  sudo nmcli radio wifi off
fi
echo "== $(date -Iseconds) =="
echo "-- wifi radio: $(nmcli radio wifi)"
echo "-- links:"; ip -br link | grep -v '^lo'
echo "-- default route:"; ip route show default || true
[ -z "$(ip route show default)" ] && echo "   (none)"
echo "-- ping 8.8.8.8:"
if ping -c 2 -W 2 8.8.8.8 >/dev/null 2>&1; then echo "   REACHABLE -> NOT offline"; exit 1; else echo "   unreachable -> offline"; fi
