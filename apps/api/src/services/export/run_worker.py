"""CLI entry point to run Export worker."""

import logging

from .worker import run_export_worker

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    run_export_worker()
