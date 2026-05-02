"""CLI entry point to run RAG worker."""

import logging

from .worker import run_rag_worker

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    run_rag_worker()
