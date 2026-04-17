"""Regression tests for the packaged desktop launcher."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from dvrs_tool import desktop


class FakeDownload:
    def __init__(self, filename: str = "dvrs-ordering-summary.pdf") -> None:
        self.filename = filename
        self.download_directory = None
        self.download_file_name = None
        self.accepted = False
        self.cancelled = False

    def downloadFileName(self) -> str:
        return self.filename

    def setDownloadDirectory(self, value: str) -> None:
        self.download_directory = value

    def setDownloadFileName(self, value: str) -> None:
        self.download_file_name = value

    def accept(self) -> None:
        self.accepted = True

    def cancel(self) -> None:
        self.cancelled = True


class DesktopRuntimeTests(unittest.TestCase):
    def test_uvicorn_config_disables_default_log_config_for_windowed_builds(self) -> None:
        config = desktop._uvicorn_config_kwargs(app=object(), host="127.0.0.1", port=8123)

        self.assertIsNone(config["log_config"])
        self.assertFalse(config["access_log"])
        self.assertEqual(config["log_level"], "warning")

    def test_ensure_standard_streams_replaces_missing_stdio(self) -> None:
        original_stdout_fallback = desktop._STDOUT_FALLBACK
        original_stderr_fallback = desktop._STDERR_FALLBACK

        try:
            with patch.object(sys, "stdout", None), patch.object(sys, "stderr", None):
                desktop._STDOUT_FALLBACK = None
                desktop._STDERR_FALLBACK = None

                desktop._ensure_standard_streams()

                self.assertIsNotNone(sys.stdout)
                self.assertIsNotNone(sys.stderr)
                self.assertTrue(hasattr(sys.stdout, "isatty"))
                self.assertTrue(hasattr(sys.stderr, "isatty"))
        finally:
            if desktop._STDOUT_FALLBACK is not None:
                desktop._STDOUT_FALLBACK.close()
            if desktop._STDERR_FALLBACK is not None:
                desktop._STDERR_FALLBACK.close()
            desktop._STDOUT_FALLBACK = original_stdout_fallback
            desktop._STDERR_FALLBACK = original_stderr_fallback

    def test_configure_runtime_logging_uses_file_logging_when_frozen(self) -> None:
        with patch.object(desktop.logging, "basicConfig") as basic_config:
            with patch.object(sys, "frozen", True, create=True):
                desktop._configure_runtime_logging()

        basic_config.assert_called_once()
        kwargs = basic_config.call_args.kwargs
        self.assertEqual(kwargs["level"], desktop.logging.WARNING)
        self.assertTrue(str(kwargs["filename"]).endswith(desktop.DESKTOP_LOG_FILENAME))

    def test_configure_runtime_logging_skips_file_logging_for_normal_console_runs(self) -> None:
        with patch.object(desktop.logging, "basicConfig") as basic_config:
            with patch.object(sys, "frozen", False, create=True):
                desktop._configure_runtime_logging()

        basic_config.assert_not_called()

    def test_prompt_for_download_path_uses_selected_save_location(self) -> None:
        download = FakeDownload()
        selected_path = Path("C:/Users/tester/Documents/custom-ordering.pdf")

        desktop._prompt_for_download_path(
            download,
            lambda default_path: (str(selected_path), "PDF Files (*.pdf)"),
            default_dir=Path("C:/Users/tester/Downloads"),
        )

        self.assertEqual(download.download_directory, str(selected_path.parent))
        self.assertEqual(download.download_file_name, selected_path.name)
        self.assertTrue(download.accepted)
        self.assertFalse(download.cancelled)

    def test_prompt_for_download_path_cancels_when_user_dismisses_dialog(self) -> None:
        download = FakeDownload()

        desktop._prompt_for_download_path(
            download,
            lambda default_path: ("", "PDF Files (*.pdf)"),
            default_dir=Path("C:/Users/tester/Downloads"),
        )

        self.assertTrue(download.cancelled)
        self.assertFalse(download.accepted)
        self.assertIsNone(download.download_directory)
        self.assertIsNone(download.download_file_name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
