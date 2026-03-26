from ...core.pipeline_events import QUEUE_COMPLIANCE
from ...core.rabbitmq import consume
from .engine import process_embedding_complete


def run_compliance_worker() -> None:
  consume(QUEUE_COMPLIANCE, process_embedding_complete)


if __name__ == "__main__":
  run_compliance_worker()
