#!/usr/bin/env sh
set -eu

if [ "$#" -lt 1 ]; then
  echo "Usage: run_worker.sh <worker-name>"
  exit 1
fi

worker="$1"

case "$worker" in
  ocr)
    exec python -m apps.api.src.services.ocr.run_worker
    ;;
  nlp)
    exec python -m apps.api.src.services.nlp.run_worker
    ;;
  embedding)
    exec python -m apps.api.src.services.embedding.run_worker
    ;;
  compliance)
    exec python -m apps.api.src.services.compliance.run_worker
    ;;
  notification)
    exec python -m apps.api.src.services.notification.run_worker
    ;;
  rag)
    exec python -m apps.api.src.services.rag.run_worker
    ;;
  llm)
    exec python -m apps.api.src.services.llm.run_worker
    ;;
  export)
    exec python -m apps.api.src.services.export.run_worker
    ;;
  *)
    echo "Unknown worker: $worker"
    exit 1
    ;;
esac
