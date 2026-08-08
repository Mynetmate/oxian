#!/bin/sh
# ============================================
# Start snmpsim test environment for oxian
# ============================================

set -e

cd "$(dirname "$0")"

if [ ! -f ".venv/bin/activate" ]; then
    echo "venv not found, creating..."
    python3 -m venv .venv
    . .venv/bin/activate
    pip install snmpsim-lextudio
    echo
else
    . .venv/bin/activate
fi

PIDS=""

stop_agents() {
    echo
    echo "Stopping agents..."
    for pid in $PIDS; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    echo "Stopped."
    exit 0
}

trap stop_agents INT TERM

start_agent() {
    name=$1
    dir=$2
    port=$3

    echo "  $name = 127.0.0.1:$port"
    snmpsim-command-responder \
        --data-dir="./data/$dir" \
        --agent-udpv4-endpoint="127.0.0.1:$port" \
        --log-level=error &
    PIDS="$PIDS $!"
}

echo "Starting snmpsim agents..."
echo

start_agent "RT-CORE-01    " core-router    1611
sleep 2
start_agent "SW-ACCESS-01  " switch-01      1612
sleep 2
start_agent "RT-BRANCH-01  " branch-router  1613
sleep 2
start_agent "MK-SW-OFFICE  " mikrotik       1614
sleep 2
start_agent "web-prod-01   " linux-server   1615

echo
echo "All agents running."
echo
echo "Test with:"
echo "  snmpget -v2c -c public 127.0.0.1:1611 1.3.6.1.2.1.1.1.0"
echo
echo "Press Ctrl+C to stop all agents..."

wait
