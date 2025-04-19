# MCP Agent Bot Conversation

This project demonstrates a multi-agent conversation system where two language model agents (BotA and BotB) interact with each other, orchestrated by a driver script. The agents utilize a local LLM served by Ollama, and the communication framework potentially leverages the Model Context Protocol (MCP), although the current implementation uses direct interactions defined within the bot scripts.

## Features

*   **Multi-Agent Interaction:** Simulates a conversation between two distinct AI bots (BotA and BotB).
*   **Local LLM Powered:** Uses a locally hosted language model via [Ollama](https://ollama.com/) (configured for `phi3` by default).
*   **Dockerized Ollama:** Includes a Docker setup to easily run the required Ollama server and automatically pull the specified model.
*   **MCP Framework:** Built using the `mcp` Python SDK for the bot servers.
*   **Conversation Logging:** Records the full conversation history with timestamps in `src/conversation_log.txt`.

## Technology Stack

*   Python 3.12+
*   [Ollama](https://ollama.com/) (running `phi3` model by default)
*   [Model Context Protocol (MCP) Python SDK](https://github.com/modelcontextprotocol/python-sdk)
*   FastAPI & Uvicorn (for bot servers)
*   OpenAI Python Client (configured for Ollama)
*   Docker

## Project Structure

```
mcp-agent/
├── Dockerfile                  # Defines the Docker image for running Ollama
├── README.md                   # This file
├── docker-entrypoint-ollama.sh # Helper script run by Dockerfile to start Ollama & pull model
└── src/
    ├── .env                    # Optional file for environment variables (e.g., OPENAI_API_KEY, if used)
    ├── bot_a.py                # Runs the MCP server for Bot A (listens on port 8001)
    ├── bot_b.py                # Runs the MCP server for Bot B (listens on port 8002)
    ├── converse.py             # Driver script orchestrating the conversation
    ├── requirements.txt        # Python dependencies
    ├── conversation_log.txt    # Log file for conversations (created on run)
    └── venv/                   # Optional: Python virtual environment directory
```

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/vishalmakwana111/mcp-agent.git
    cd mcp-agent
    ```
2.  **Install Docker:** Ensure you have Docker installed and running. ([Install Docker](https://docs.docker.com/get-docker/))
3.  **Build the Ollama Docker Image:** This image includes Ollama and automatically pulls the required model (`phi3` by default) when started.
    ```bash
    docker build -t ollama-server-with-model .
    ```
4.  **Set up Python Environment:** It's recommended to use a virtual environment for the Python scripts.
    ```bash
    # Navigate to the source directory
    cd src

    # Create a virtual environment (if you haven't already)
    python -m venv venv

    # Activate the virtual environment
    # On Windows (Powershell):
    .\venv\Scripts\Activate.ps1
    # On macOS/Linux:
    # source venv/bin/activate

    # Install Python dependencies
    pip install -r requirements.txt
    ```

## Running the Application

1.  **Start the Ollama Docker Container:** Run the Ollama server in the background. This command also maps the necessary port.
    ```bash
    # Run this from the project root directory (mcp-agent/)
    docker run -d --rm --name ollama -p 11434:11434 ollama-server-with-model
    ```
    *   You can check the logs to see the model being pulled: `docker logs -f ollama` (Press Ctrl+C to stop following). Wait for the "Model pull complete" message before proceeding.

2.  **Start Bot A:**
    *   Open a **new terminal**.
    *   Navigate to the `src` directory: `cd path/to/mcp-agent/src`
    *   Activate the virtual environment (e.g., `.\venv\Scripts\Activate.ps1`).
    *   Run the bot: `python bot_a.py`

3.  **Start Bot B:**
    *   Open **another new terminal**.
    *   Navigate to the `src` directory: `cd path/to/mcp-agent/src`
    *   Activate the virtual environment.
    *   Run the bot: `python bot_b.py`

4.  **Run the Conversation Driver:**
    *   Open **yet another new terminal**.
    *   Navigate to the `src` directory: `cd path/to/mcp-agent/src`
    *   Activate the virtual environment.
    *   Run the driver script: `python converse.py`

## Configuration

*   **LLM Model:** The model used by the bots (`phi3`) is configured in `bot_a.py`, `bot_b.py`, and `docker-entrypoint-ollama.sh`. Change the model name in all three places if you want to use a different Ollama model.
*   **Ollama URL:** The bots connect to `http://localhost:11434/v1`. This is configured in `bot_a.py` and `bot_b.py`.
*   **Bot Prompts:** The system prompts defining the bots' personas are set within `bot_a.py` and `bot_b.py`.
*   **Log File:** Conversation output is saved to `src/conversation_log.txt`.
*   **Conversation Length/Delay:** The number of turns and the delay between turns are set in the `for` loop and `asyncio.sleep` call within `src/converse.py`.