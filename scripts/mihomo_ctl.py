#!/usr/bin/env python3
"""Daily mihomo lifecycle, provider, node, latency, and group-selection commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import secrets
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
DATA_DIR = SKILL_DIR.parent / ".mihomo"


def initialize_config(home: Path, config: Path) -> bool:
    """Create a local-only usable default without replacing user configuration."""
    if config.exists():
        return False
    home.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "# Created by mihomo_ctl.py; local HTTP and SOCKS listeners are enabled.\n"
        "port: 7890\n"
        "socks-port: 7891\n"
        "allow-lan: false\n"
        "mode: rule\n"
        "log-level: info\n\n"
        "external-controller: 127.0.0.1:9090\n"
        f"secret: {secrets.token_urlsafe(24)!r}\n\n"
        "proxy-groups:\n"
        "  - name: PROXY\n"
        "    type: select\n"
        "    proxies:\n"
        "      - DIRECT\n\n"
        "rules:\n"
        "  - MATCH,PROXY\n"
    )
    return True


def has_proxy_source(config: Path) -> bool:
    """A startable proxy profile must define nodes or a subscription provider."""
    if not config.exists():
        return False
    return bool(re.search(r"^(?:proxies|proxy-providers):\s*$", config.read_text(errors="replace"), re.MULTILINE))


def scalar(config: Path, key: str) -> str | None:
    if not config.exists():
        return None
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.*?)\s*$")
    for line in config.read_text(errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip("'\"")
    return None


def paths(args):
    home = Path(args.home).expanduser()
    return home, Path(args.config).expanduser() if args.config else home / "config.yaml", home / "mihomo.pid", home / "mihomo.log"


def core(home: Path) -> Path:
    result = subprocess.run([sys.executable, str(SKILL_DIR / "ensure_mihomo.py"), "--print-path"], capture_output=True, text=True, check=True)
    path = Path(result.stdout.strip())
    if not path.exists():
        subprocess.run([sys.executable, str(SKILL_DIR / "ensure_mihomo.py"), "--ensure"], check=True)
    return path


def is_live(args, config: Path) -> bool:
    try:
        api(args, config, "/version")
        return True
    except Exception:
        return False


def stop_mihomo_instances(core_bin: Path):
    if sys.platform == "win32":
        ps_cmd = f"Get-Process mihomo -ErrorAction SilentlyContinue | Where-Object {{ $_.Path -like '*{core_bin.name}*' }} | Stop-Process -Force"
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
    else:
        subprocess.run(["pkill", "-f", str(core_bin)], capture_output=True)


def controller(args, config: Path) -> tuple[str, str]:
    address = args.controller or scalar(config, "external-controller") or "127.0.0.1:9090"
    secret = os.environ.get("MIHOMO_SECRET") or scalar(config, "secret")
    if not secret:
        raise RuntimeError("Set MIHOMO_SECRET or configure a top-level secret in config.yaml")
    return "http://" + address.removeprefix("http://").removeprefix("https://"), secret


def api(args, config: Path, path: str, method="GET", payload=None):
    base, secret = controller(args, config)
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(base + path, data=body, method=method, headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read() or b"{}")


def require_running(args, config: Path):
    if not is_live(args, config):
        raise RuntimeError("mihomo is not running; use start first")


def live_status(args, config: Path) -> dict:
    """Return status and effective configuration from the live controller.

    A PID file is only bookkeeping for a process launched by this helper.  It
    cannot establish that the process is a healthy mihomo instance, nor can it
    describe runtime-only changes (for example a TUN toggle).  The controller
    is the authoritative source for both pieces of information.
    """
    try:
        version = api(args, config, "/version")
        current_config = api(args, config, "/configs")
    except Exception as exc:
        return {
            "running": False,
            "config": None,
            "error": f"live controller is unavailable: {exc}",
        }
    return {"running": True, "version": version, "config": current_config}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", default=str(DATA_DIR))
    parser.add_argument("--config")
    parser.add_argument("--controller")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create the default local HTTP/SOCKS config if absent")
    sub.add_parser("start"); sub.add_parser("stop")
    sub.add_parser("status", help="Query live controller status and effective configuration")
    sub.add_parser("validate")
    logs = sub.add_parser("logs"); logs.add_argument("--tail", type=int, default=80)
    sub.add_parser("providers")
    nodes = sub.add_parser("nodes"); nodes.add_argument("provider")
    speed = sub.add_parser("speedtest"); speed.add_argument("provider"); speed.add_argument("--wait", type=int, default=20)
    select = sub.add_parser("select"); select.add_argument("group"); select.add_argument("node")
    tun = sub.add_parser("tun", help="Temporarily enable or disable TUN on the running core")
    tun.add_argument("state", choices=["on", "off"])
    args = parser.parse_args()
    home, config, pid_path, log_path = paths(args)
    try:
        if args.command == "init":
            print(f"{'created' if initialize_config(home, config) else 'kept existing'} config: {config}"); return 0
        if args.command == "validate":
            subprocess.run([str(core(home)), "-t", "-d", str(home), "-f", str(config)], check=True); return 0
        if args.command == "start":
            if is_live(args, config):
                print("mihomo already running (detected via controller API)")
                return 0
            created = initialize_config(home, config)
            if created: print(f"created default config with HTTP :7890 and SOCKS :7891: {config}")
            if not has_proxy_source(config):
                raise RuntimeError("No subscription or static proxy is configured. Ask the user for a subscription URL or node configuration before starting.")
            subprocess.run([str(core(home)), "-t", "-d", str(home), "-f", str(config)], check=True)
            home.mkdir(parents=True, exist_ok=True)
            with log_path.open("a") as log:
                process = subprocess.Popen([str(core(home)), "-d", str(home), "-f", str(config)], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            time.sleep(1)
            if process.poll() is not None: raise RuntimeError(f"mihomo exited; inspect {log_path}")
            print(f"mihomo started (pid {process.pid})"); return 0
        if args.command == "stop":
            if not is_live(args, config):
                print("mihomo is not running")
                return 0
            stop_mihomo_instances(core(home))
            for _ in range(20):
                if not is_live(args, config):
                    break
                time.sleep(0.25)
            print("mihomo stopped"); return 0
        if args.command == "status":
            print(json.dumps(live_status(args, config), ensure_ascii=False, indent=2)); return 0
        if args.command == "logs":
            print("".join(log_path.read_text(errors="replace").splitlines(True)[-args.tail:]), end=""); return 0
        require_running(args, config)
        if args.command == "providers":
            providers = api(args, config, "/providers/proxies").get("providers", {})
            for name, value in providers.items(): print(f"{name}\t{len(value.get('proxies', []))} nodes")
        elif args.command == "nodes":
            name = urllib.parse.quote(args.provider, safe="")
            items = api(args, config, f"/providers/proxies/{name}").get("proxies", [])
            for item in items:
                history = item.get("history") or []; delay = history[-1].get("delay", "-") if history else "-"
                print(f"{delay} ms\t{item.get('name', '<unnamed>')}")
        elif args.command == "speedtest":
            name = urllib.parse.quote(args.provider, safe="")
            api(args, config, f"/providers/proxies/{name}", "PUT"); api(args, config, f"/providers/proxies/{name}/healthcheck")
            time.sleep(args.wait); items = api(args, config, f"/providers/proxies/{name}").get("proxies", [])
            rows = []
            for item in items:
                history = item.get("history") or []; delay = history[-1].get("delay", 0) if history else 0
                if isinstance(delay, int) and delay > 0: rows.append((delay, item.get("name", "<unnamed>")))
            for delay, name in sorted(rows): print(f"{delay} ms\t{name}")
            print(f"measured {len(rows)}/{len(items)}")
        elif args.command == "select":
            group = urllib.parse.quote(args.group, safe="")
            api(args, config, f"/proxies/{group}", "PUT", {"name": args.node}); print(f"selected {args.node} for {args.group}")
        elif args.command == "tun":
            enabled = args.state == "on"
            api(args, config, "/configs", "PATCH", {"tun": {"enable": enabled}})
            print(f"TUN {'enabled' if enabled else 'disabled'} for the running instance (not persisted across restart)")
    except Exception as exc:
        print(f"mihomo ctl error: {exc}", file=sys.stderr); return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
