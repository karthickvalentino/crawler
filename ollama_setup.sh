#!/bin/sh
set -e

echo "Waiting for Ollama to be ready..."
while ! curl -s -f http://ollama:11434/api/tags > /dev/null; do
  sleep 1
done

echo "Ollama is ready. Pulling models..."
curl http://ollama:11434/api/pull -d '{"name": "llama3.2:latest"}'
curl http://ollama:11434/api/pull -d '{"name": "llava:latest"}'
echo "Model pull commands sent."
