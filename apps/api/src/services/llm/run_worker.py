"""CLI entry point to run LLM worker."""

import logging

from .worker import run_llm_worker

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    run_llm_worker()
