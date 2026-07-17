#!/usr/bin/env python3
"""Start the local hosted AirSpaceSim API and web app together."""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_DIR = PROJECT_ROOT / "apps" / "api"
WEB_DIR = PROJECT_ROOT / "apps" / "web"
DEFAULT_DEMO_TEMPLATE = (
    PROJECT_ROOT / "airspaces" / "nerava_fir" / "scenarios" / "mixed_traffic.v1.json"
)
DEFAULT_DEMO_AIRSPACE = PROJECT_ROOT / "airspaces" / "nerava_fir" / "airspace.v1.json"


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def _default_python() -> str:
    venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _stream_process_output(name: str, process: subprocess.Popen[str]) -> None:
    assert process.stdout is not None
    for line in process.stdout:
        print(f"[{name}] {line.rstrip()}", flush=True)


def _start_process(
    name: str,
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.Popen[str]:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    thread = threading.Thread(
        target=_stream_process_output,
        args=(name, process),
        daemon=True,
    )
    thread.start()
    return process


def _wait_for_url(url: str, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=2):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def _is_port_available(host: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, port))
    except OSError:
        return False
    return True


def _print_port_in_use_message(
    host: str,
    busy_ports: list[tuple[str, int]],
    api_port: int,
    web_port: int,
) -> None:
    print(
        "Cannot start AirSpaceSim hosted dev servers because a required port is busy.",
        file=sys.stderr,
        flush=True,
    )
    print("", file=sys.stderr, flush=True)
    print("Busy ports:", file=sys.stderr, flush=True)
    for service_name, port in busy_ports:
        print(f"  {service_name}: {host}:{port}", file=sys.stderr, flush=True)
    print("", file=sys.stderr, flush=True)
    print("Check the processes using these ports:", file=sys.stderr, flush=True)
    for _, port in busy_ports:
        print(f"  lsof -i :{port} -sTCP:LISTEN", file=sys.stderr, flush=True)
    print("", file=sys.stderr, flush=True)
    print(
        "Then either stop the old process or choose different ports:",
        file=sys.stderr,
        flush=True,
    )
    print(
        "  python3 scripts/start_hosted_dev.py "
        f"--seed --api-port {api_port + 10} --web-port {web_port + 16}",
        file=sys.stderr,
        flush=True,
    )
    print("", file=sys.stderr, flush=True)
    print(
        f"Expected API address: http://{host}:{api_port}/health",
        file=sys.stderr,
        flush=True,
    )
    print(
        f"Expected web address: http://{host}:{web_port}",
        file=sys.stderr,
        flush=True,
    )


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        process.terminate()
    else:
        process.send_signal(signal.SIGTERM)


def _stop_processes(processes: list[subprocess.Popen[str]]) -> None:
    for process in processes:
        _terminate_process(process)
    for process in processes:
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()


def _seed_demo(args: argparse.Namespace, api_base_url: str, web_base_url: str) -> None:
    command = [
        _default_python(),
        str(PROJECT_ROOT / "scripts" / "seed_hosted_demo.py"),
        "--api-base-url",
        api_base_url,
        "--web-base-url",
        web_base_url,
        "--airspace",
        args.seed_airspace,
        "--template",
        args.seed_template,
    ]
    if args.seed_stagger_seconds is not None:
        command.extend(["--stagger-seconds", str(args.seed_stagger_seconds)])
    subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start AirSpaceSim API and web dev servers together.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for both dev servers.")
    parser.add_argument("--api-port", type=int, default=8000, help="API port.")
    parser.add_argument("--web-port", type=int, default=5174, help="Web app port.")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Create a demo run after the API starts.",
    )
    parser.add_argument(
        "--seed-airspace",
        default=_repo_relative(DEFAULT_DEMO_AIRSPACE),
        help="Airspace JSON path to use when --seed is set.",
    )
    parser.add_argument(
        "--seed-template",
        default=_repo_relative(DEFAULT_DEMO_TEMPLATE),
        help="Scenario template JSON path to use when --seed is set.",
    )
    parser.add_argument(
        "--seed-stagger-seconds",
        type=float,
        default=None,
        help="Optional seed stagger seconds override. Use 0 for all aircraft quickly.",
    )
    parser.add_argument(
        "--api-ready-timeout",
        type=float,
        default=30.0,
        help="Seconds to wait for API /health before optional seeding.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_base_url = f"http://{args.host}:{args.api_port}"
    web_base_url = f"http://{args.host}:{args.web_port}"

    busy_ports = [
        (service_name, port)
        for service_name, port in [
            ("API", args.api_port),
            ("Web", args.web_port),
        ]
        if not _is_port_available(args.host, port)
    ]
    if busy_ports:
        _print_port_in_use_message(
            args.host,
            busy_ports,
            args.api_port,
            args.web_port,
        )
        return 1

    web_env = os.environ.copy()
    web_env.setdefault("VITE_API_BASE_URL", api_base_url)

    processes: list[subprocess.Popen[str]] = []

    def stop_from_suspend_signal(signum: int, frame) -> None:  # noqa: ARG001
        print(
            "\nCtrl-Z would leave child servers running; stopping instead. "
            "Use Ctrl-C to stop AirSpaceSim dev servers.",
            flush=True,
        )
        _stop_processes(processes)
        raise SystemExit(0)

    if hasattr(signal, "SIGTSTP"):
        signal.signal(signal.SIGTSTP, stop_from_suspend_signal)

    try:
        api_process = _start_process(
            "api",
            [
                _default_python(),
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                args.host,
                "--port",
                str(args.api_port),
                "--reload",
            ],
            API_DIR,
        )
        processes.append(api_process)

        web_process = _start_process(
            "web",
            [
                "npm",
                "run",
                "dev",
                "--",
                "--host",
                args.host,
                "--port",
                str(args.web_port),
                "--strictPort",
            ],
            WEB_DIR,
            env=web_env,
        )
        processes.append(web_process)

        print("", flush=True)
        print("AirSpaceSim hosted dev servers starting:", flush=True)
        print(f"- API: {api_base_url}/health", flush=True)
        print(f"- Web: {web_base_url}", flush=True)
        print("Press Ctrl-C to stop both servers.", flush=True)
        print("", flush=True)

        if args.seed:
            health_url = f"{api_base_url}/health"
            if _wait_for_url(health_url, args.api_ready_timeout):
                _seed_demo(args, api_base_url, web_base_url)
            else:
                print(
                    f"API did not become ready at {health_url}; skipping seed.",
                    file=sys.stderr,
                    flush=True,
                )

        while True:
            for process in processes:
                if process.poll() is not None:
                    _stop_processes(processes)
                    return process.returncode or 0
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping AirSpaceSim hosted dev servers...", flush=True)
        return 0
    finally:
        _stop_processes(processes)


if __name__ == "__main__":
    raise SystemExit(main())
