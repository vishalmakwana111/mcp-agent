#!/bin/bash
set -e

# Start Ollama serve in the background
echo "Starting Ollama serve in background..."
/bin/ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready by polling the API endpoint
echo "Waiting for Ollama server to be ready..."
retries=10
while ! curl -s http://localhost:11434 > /dev/null; do
    retries=$((retries-1))
    if [ $retries -eq 0 ]; then
        echo "Ollama server failed to start after multiple retries. Exiting."
        kill $OLLAMA_PID # Attempt to kill background process
        exit 1
    fi
    echo "Ollama not ready yet, sleeping for 2 seconds... ($retries retries left)"
    sleep 2
done
echo "Ollama server is ready."

# Pull the desired model (phi3)
echo "Pulling Ollama model (phi3)..."
ollama pull phi3
echo "Model pull complete."

# Now, keep the container alive by waiting for the background ollama process
echo "Ollama setup complete. Tailing logs or waiting for process $OLLAMA_PID..."

# Option 1: Wait specifically for the Ollama process
wait $OLLAMA_PID

# Option 2: Tail logs (alternative way to keep container running, uncomment if preferred)
# echo "Tailing Ollama logs (press Ctrl+C to stop container)..."
# tail -f /root/.ollama/logs/server.log

echo "Ollama process $OLLAMA_PID finished." 