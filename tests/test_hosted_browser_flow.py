import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest


def _free_port() -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]
    except PermissionError:
        pytest.skip("Local socket binding is not permitted in this environment.")


def _wait_for_http(url: str, *, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1.0) as response:
                if response.status < 500:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for {url}")


def test_hosted_browser_flow_supports_run_creation_and_commands(tmp_path):
    if os.environ.get("AIRSPACESIM_BROWSER_SMOKE") != "1":
        pytest.skip("Browser smoke test disabled (set AIRSPACESIM_BROWSER_SMOKE=1).")

    playwright = pytest.importorskip("playwright.sync_api")
    repo_root = Path(__file__).resolve().parents[1]
    web_dist = repo_root / "apps" / "web" / "dist"
    if not web_dist.exists():
        pytest.skip("Hosted web build missing. Build apps/web before browser smoke.")

    api_env = dict(os.environ)
    api_env["AIRSPACESIM_API_DATABASE_URL"] = f"sqlite:///{tmp_path / 'hosted-smoke.db'}"
    api_env["AIRSPACESIM_API_AUTO_CREATE_SCHEMA"] = "1"

    api_server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=repo_root / "apps" / "api",
        env=api_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    web_port = _free_port()
    web_server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(web_port)],
        cwd=web_dist,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    console_errors: list[str] = []
    page_errors: list[str] = []
    try:
        _wait_for_http("http://127.0.0.1:8000/health")
        _wait_for_http(f"http://127.0.0.1:{web_port}/index.html")

        with playwright.sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.on(
                "console",
                lambda msg: console_errors.append(msg.text)
                if msg.type == "error"
                else None,
            )
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            page.goto(f"http://127.0.0.1:{web_port}/runs", wait_until="networkidle")
            page.get_by_label("Run name").fill("Hosted smoke run")
            page.get_by_role("button", name="Create Draft Run").click()
            page.get_by_role("heading", name="Hosted smoke run").wait_for()
            page.get_by_role("button", name="Launch").click()
            page.get_by_role("button", name="Pause").wait_for()

            add_aircraft_form = page.locator("form").filter(
                has=page.get_by_text("Add Track"),
            )
            add_aircraft_form.get_by_label("Aircraft ID").fill("AC901")
            add_aircraft_form.get_by_label("Callsign").fill("OPS901")
            add_aircraft_form.get_by_label("Route ID").fill("UA612")
            add_aircraft_form.get_by_label("Speed (kt)").fill("420")
            add_aircraft_form.get_by_label("Flight level").fill("350")
            add_aircraft_form.get_by_role("button", name="Add Track").click()

            page.get_by_text("1/1").wait_for()
            page.get_by_role("heading", name="Track added").wait_for()
            page.get_by_role("heading", name="OPS901").wait_for()

            add_aircraft_form.get_by_label("Aircraft ID").fill("AC902")
            add_aircraft_form.get_by_label("Callsign").fill("OPS902")
            add_aircraft_form.get_by_label("Route ID").fill("UA612")
            add_aircraft_form.get_by_label("Speed (kt)").fill("410")
            add_aircraft_form.get_by_label("Flight level").fill("330")
            add_aircraft_form.get_by_role("button", name="Add Track").click()

            page.get_by_text("2/2").wait_for()
            page.get_by_role("button", name="OPS902").click()
            page.get_by_role("heading", name="OPS902").wait_for()

            browser.close()
    finally:
        web_server.terminate()
        api_server.terminate()
        web_server.wait(timeout=10)
        api_server.wait(timeout=10)

    assert page_errors == [], f"Page errors detected: {page_errors}"
    assert console_errors == [], f"Console errors detected: {console_errors}"
