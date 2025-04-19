# Use the official Ollama base image
FROM ollama/ollama:latest

# Install curl for readiness check in entrypoint
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the new entrypoint script and make it executable
COPY docker-entrypoint-ollama.sh /usr/local/bin/docker-entrypoint-ollama.sh
RUN chmod +x /usr/local/bin/docker-entrypoint-ollama.sh

# Expose the Ollama API port
EXPOSE 11434

# Set the entrypoint to our custom script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint-ollama.sh"]

# No default command needed, entrypoint handles the main process
CMD []

# No Python installation needed here

# Set the working directory (optional, can be removed)
WORKDIR /app

# No Python requirements needed

# No application code needed

# No custom entrypoint script needed 