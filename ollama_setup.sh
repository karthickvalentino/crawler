#!/bin/sh
set -e

echo "Waiting for Ollama to be ready..."
while ! curl -s -f http://ollama:11434/api/tags > /dev/null; do
  sleep 1
done

echo "Ollama is ready. Pulling llama3.2:latest model..."
curl http://ollama:11434/api/pull -d '{"name": "llama3.2:latest"}'
echo "Model pull command sent."
