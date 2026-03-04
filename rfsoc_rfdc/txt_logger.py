import os
import logging
from pathlib import Path


class TxtLogger:
    """
    Centralized logger for text-based metrics and status logs.
    Manages output directories to avoid hardcoded paths across the codebase.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TxtLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_dir="wave_files"):
        if self._initialized:
            return

        # Use relative path 'wave_files' from the current working directory.
        # If rfsoc_rfdc is installed as a package, this will be relative to where the script is run.
        # For typical Jupyter usage, this is the notebook directory.

        self.log_dir = Path(log_dir)
        try:
            if not self.log_dir.exists():
                self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.warning(
                f"Failed to create log directory {self.log_dir}: {e}")
            # Fallback to current directory
            self.log_dir = Path(".")

        self._initialized = True

    def get_log_dir(self) -> Path:
        return self.log_dir

    def log_metrics(self, filename: str, metrics_line: str, mode='w'):
        """
        Log a string of metrics to a file.

        Args:
            filename: Name of the log file (e.g., "ch0_metrics.log")
            metrics_line: Content to write
            mode: File open mode ('w' for overwrite, 'a' for append)
        """
        file_path = self.log_dir / filename
        try:
            with open(file_path, mode) as f:
                f.write(metrics_line)
                if not metrics_line.endswith('\n'):
                    f.write('\n')
        except Exception as e:
            logging.error(f"TxtLogger failed to write to {file_path}: {e}")

    def get_file_path(self, filename: str) -> str:
        """Returns the full path for a given filename within the log directory."""
        return str(self.log_dir / filename)


# Global instance
_txt_logger = TxtLogger()


def get_txt_logger():
    return _txt_logger
