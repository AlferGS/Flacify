import faulthandler
import logging
import os
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

from app.windows import MainFluentWindow

_LOG_DIR: Path | None = None
_CRASH_STREAM = None

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def _debug_enabled() -> bool:
    """
    Debug/diagnostics mode.

    Priority:
      1. explicit FLACIFY_DEBUG env var;
      2. source run => enabled by default;
      3. frozen exe => disabled by default.
    """
    raw = os.getenv("FLACIFY_DEBUG", "").strip().lower()

    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False

    return not getattr(sys, "frozen", False)


_DEBUG = _debug_enabled()


def _resolve_log_dir() -> Path:
    """
    Resolve writable log directory for debug mode.

    For frozen exe: %LOCALAPPDATA%/Flacify/logs
    For source run: ./logs
    If not writable: fallback to TEMP/FlacifyLogs
    """
    if getattr(sys, "frozen", False):
        local_appdata = os.getenv("LOCALAPPDATA")
        base = Path(local_appdata) if local_appdata else Path.home() / "AppData" / "Local"
        app_dir = base / "Flacify"
    else:
        app_dir = Path.cwd()

    log_dir = app_dir / "logs"

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        probe = log_dir / ".flacify_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return log_dir
    except OSError:
        temp = os.getenv("TEMP") or os.getenv("TMP") or str(Path.home())
        fallback = Path(temp) / "FlacifyLogs"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _install_diagnostics() -> None:
    """
    Install file logging, excepthooks and faulthandler only in debug mode.

    In normal release mode all logging is disabled and no log files are created.
    """
    global _LOG_DIR, _CRASH_STREAM

    if not _DEBUG:
        # Silence all logging calls from application modules.
        logging.disable(logging.CRITICAL)
        return

    _LOG_DIR = _resolve_log_dir()
    log_file = _LOG_DIR / "flacify.log"
    crash_file = _LOG_DIR / "crash.log"

    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(threadName)s | %(name)s | %(message)s",
        encoding="utf-8",
        force=True,
    )

    logger = logging.getLogger("main")

    def _excepthook(exc_type, exc, tb):
        logger.critical("Uncaught exception", exc_info=(exc_type, exc, tb))
        traceback.print_exception(exc_type, exc, tb)

    sys.excepthook = _excepthook

    if hasattr(threading, "excepthook"):
        def _thread_excepthook(args):
            logger.critical(
                "Uncaught thread exception",
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )

        threading.excepthook = _thread_excepthook

    try:
        _CRASH_STREAM = open(crash_file, "a", encoding="utf-8")
        _CRASH_STREAM.write(
            f"\n--- run start {datetime.now().isoformat(timespec='seconds')} ---\n"
        )
        _CRASH_STREAM.flush()
        faulthandler.enable(_CRASH_STREAM)
    except OSError:
        logger.warning("Cannot open crash log: %s", crash_file)


def main() -> int:
    _install_diagnostics()

    logger = logging.getLogger("main")
    if _DEBUG:
        logger.info("start application; debug=%s; log_dir=%s", _DEBUG, _LOG_DIR)

    try:
        app = QApplication(sys.argv)
    except Exception:
        if _DEBUG:
            logger.exception("Failed to create QApplication")
        return 1

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    try:
        window = MainFluentWindow()
    except Exception:
        if _DEBUG:
            logger.exception("Failed to create MainFluentWindow")
        return 1

    window.setStyleSheet("background-color: #000000")
    window.show()

    if _DEBUG:
        app.aboutToQuit.connect(lambda: logger.info("aboutToQuit"))

    try:
        rc = app.exec_()
        if _DEBUG:
            logger.info("event loop exited with code %s", rc)
        return rc
    except Exception:
        if _DEBUG:
            logger.exception("Error in Qt event loop")
        return 1
    finally:
        if _DEBUG:
            logger.info("close application")


if __name__ == "__main__":
    sys.exit(main())