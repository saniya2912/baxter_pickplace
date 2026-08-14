#!/bin/bash
# Fix the eth0/wlan0 subnet collision on the laptop.
#
# eth0 (-> Baxter) and wlan0 (-> lab PC) both sit on 192.168.0.0/24, so
# without explicit host routes the lower-metric interface wins for ALL
# traffic in that range -- including traffic meant for the other one.
# These routes are session-only (the kernel doesn't persist them), so this
# needs to be re-run after every laptop reboot. See 7aug_physical.md and
# 13aug_physical.md for the original diagnosis (including a past mistake
# pointing Baxter's route at the wrong interface).
#
# Run this on the laptop after every reboot:
#   bash setup_routes.sh

set -e

LAB_PC_IP="192.168.0.104"
LAB_PC_IFACE="wlan0"
BAXTER_IP="192.168.0.99"
BAXTER_IFACE="eth0"

add_route_if_missing() {
    local ip="$1"
    local iface="$2"
    if ip route show | grep -q "^${ip}/32 dev ${iface}"; then
        echo "  ${ip}/32 dev ${iface} already set, skipping."
    else
        echo "  adding ${ip}/32 dev ${iface} ..."
        sudo ip route add "${ip}/32" dev "${iface}"
    fi
}

echo "=== Setting up host routes ==="
add_route_if_missing "$LAB_PC_IP" "$LAB_PC_IFACE"
add_route_if_missing "$BAXTER_IP" "$BAXTER_IFACE"

echo ""
echo "=== Current relevant routes ==="
ip route show | grep -E "$LAB_PC_IP|$BAXTER_IP" || echo "  (none found -- something's wrong)"
