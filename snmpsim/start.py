"""SNMPSim Launcher for Oxian - Multi-device Loopback Simulation.

Spawns 5 simulated network agents on 127.0.0.1 - 127.0.0.5 (Port 161)
and cleanly kills all child processes on Ctrl+C (KeyboardInterrupt).
"""

from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import time

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

AGENTS = [
    {"name": "RT-CORE-01", "ip": "127.0.0.1", "dir": DATA_DIR / "core-router"},
    {"name": "SW-ACCESS-01", "ip": "127.0.0.2", "dir": DATA_DIR / "switch-01"},
    {"name": "RT-BRANCH-01", "ip": "127.0.0.3", "dir": DATA_DIR / "branch-router"},
    {"name": "MK-SW-OFFICE", "ip": "127.0.0.4", "dir": DATA_DIR / "mikrotik"},
    {"name": "web-prod-01", "ip": "127.0.0.5", "dir": DATA_DIR / "linux-server"},
]

processes: list[subprocess.Popen] = []


def kill_all() -> None:
    print("\n[!] Stopping all snmpsim agents...")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass

    # Ensure all snmpsim responder executables on Windows are terminated
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/IM", "snmpsim-command-responder.exe"], capture_output=True)

    print("[✓] All snmpsim agents stopped successfully.\n")


def signal_handler(sig: int, frame: object) -> None:
    kill_all()
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 60)
    print("  Oxian SNMP Simulator (Loopback Multi-Device Lab)")
    print("=" * 60)

    for agent in AGENTS:
        cmd = [
            sys.executable,
            "-m",
            "snmpsim.commands.responder",
            f"--data-dir={agent['dir']}",
            f"--agent-udpv4-endpoint={agent['ip']}:161",
            "--log-level=error",
        ]
        # Fallback to direct executable if module is not invoked
        try:
            proc = subprocess.Popen(
                ["snmpsim-command-responder", f"--data-dir={agent['dir']}", f"--agent-udpv4-endpoint={agent['ip']}:161", "--log-level=error"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        processes.append(proc)
        print(f"  [+] {agent['name']:<15} -> {agent['ip']}:161 (Running)")
        time.sleep(0.5)

    print("\n[✓] All 5 agents are active and listening on Port 161.")
    print("    Test scanning in backend API with target: 127.0.0.1 (port: 161)")
    print("\n>>> Press Ctrl+C at any time to shutdown all agents <<<\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        kill_all()


if __name__ == "__main__":
    main()
