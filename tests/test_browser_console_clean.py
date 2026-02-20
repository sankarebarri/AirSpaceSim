import os
import socket
import subprocess
import sys
import time

import pytest

from airspacesim.cli.commands import initialize_project


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_browser_console_remains_clean_for_generated_map(tmp_path, monkeypatch):
    if os.environ.get("AIRSPACESIM_BROWSER_SMOKE") != "1":
        pytest.skip("Browser smoke test disabled (set AIRSPACESIM_BROWSER_SMOKE=1).")

    playwright = pytest.importorskip("playwright.sync_api")
    monkeypatch.chdir(tmp_path)
    initialize_project()

    port = _free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)],
        cwd=tmp_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    console_errors = []
    page_errors = []
    try:
        # Give server a moment to start.
        time.sleep(0.5)
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
            page.goto(f"http://127.0.0.1:{port}/templates/map.html", wait_until="networkidle")
            page.wait_for_timeout(2000)
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)

    assert page_errors == [], f"Page errors detected: {page_errors}"
    assert console_errors == [], f"Console errors detected: {console_errors}"
