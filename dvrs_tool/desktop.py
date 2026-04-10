"""Desktop launcher for the DVRS planner."""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from .api import create_app
from .exceptions import MissingDependencyError


APP_TITLE = "DVRS In-Band Planner"
HOST = "127.0.0.1"
HEALTH_PATH = "/health"
SERVER_START_TIMEOUT_SECONDS = 15.0


@dataclass
class DesktopRuntime:
    """Own the embedded API server and desktop window lifecycle."""

    host: str = HOST

    def __post_init__(self) -> None:
        self._port: int | None = None
        self._thread: threading.Thread | None = None
        self._server = None
        self._startup_error: BaseException | None = None

    @property
    def base_url(self) -> str:
        if self._port is None:
            raise RuntimeError("Desktop runtime has not started the embedded server yet.")
        return f"http://{self.host}:{self._port}"

    def start(self) -> None:
        self._port = _reserve_local_port(self.host)
        self._thread = threading.Thread(target=self._run_server, name="dvrs-desktop-server", daemon=True)
        self._thread.start()
        self._wait_for_server()

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5.0)

    def _run_server(self) -> None:
        try:
            from uvicorn import Config, Server
        except ImportError as exc:
            self._startup_error = MissingDependencyError(
                code="MISSING_UVICORN_DEPENDENCY",
                message="The desktop runtime requires the API server dependency set.",
                details={
                    "missing_dependency": str(exc),
                    "hint": "Install requirements.txt before launching the desktop app.",
                },
            )
            return

        try:
            app = create_app()
            config = Config(
                app=app,
                host=self.host,
                port=self._port,
                log_level="warning",
                access_log=False,
                server_header=False,
                date_header=False,
            )
            self._server = Server(config)
            self._server.run()
        except BaseException as exc:
            self._startup_error = exc

    def _wait_for_server(self) -> None:
        deadline = time.monotonic() + SERVER_START_TIMEOUT_SECONDS
        health_url = f"{self.base_url}{HEALTH_PATH}"

        while time.monotonic() < deadline:
            if self._startup_error is not None:
                raise RuntimeError("The embedded DVRS server failed to start.") from self._startup_error
            if self._thread is not None and not self._thread.is_alive():
                raise RuntimeError("The embedded DVRS server stopped before the desktop window opened.")
            try:
                with urllib.request.urlopen(health_url, timeout=1.0) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.15)

        raise TimeoutError("Timed out while starting the embedded DVRS server.")


def main() -> int:
    _configure_qt_environment()
    runtime = DesktopRuntime()
    runtime.start()

    try:
        return _run_qt_window(runtime)
    finally:
        runtime.stop()


def _run_qt_window(runtime: DesktopRuntime) -> int:
    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
        from PySide6.QtWebEngineWidgets import QWebEngineView
    except ImportError as exc:
        raise MissingDependencyError(
            code="MISSING_DESKTOP_DEPENDENCY",
            message="Desktop window dependencies are not installed.",
            details={
                "missing_dependency": str(exc),
                "hint": "Install requirements-desktop.txt before launching the desktop app.",
            },
        ) from exc

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle(APP_TITLE)
            self.resize(1440, 960)

            self.browser = QWebEngineView(self)
            self.browser.load(QUrl(f"{runtime.base_url}/"))
            self.browser.renderProcessTerminated.connect(self._handle_render_process_terminated)
            self.setCentralWidget(self.browser)

        def _handle_render_process_terminated(self, termination_status, exit_code) -> None:
            QMessageBox.critical(
                self,
                APP_TITLE,
                (
                    "The embedded desktop renderer stopped unexpectedly.\n\n"
                    f"Status: {termination_status}\nExit code: {exit_code}"
                ),
            )
            self.close()

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    window = MainWindow()
    window.show()
    return app.exec()


def _configure_qt_environment() -> None:
    # Keep Chromium internals quiet in packaged runs and avoid sandbox issues
    # that can occur in frozen desktop builds on locked-down endpoints.
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-logging")
    os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")


def _reserve_local_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


if __name__ == "__main__":
    raise SystemExit(main())
