"""MCP Server implementation for Bot A."""

import logging
# import os # Unused
import uvicorn
from fastapi import FastAPI
# import openai # Unused
from openai import AsyncOpenAI, APIError
# from dotenv import load_dotenv # Not using .env for Ollama
import mcp.types as types
from mcp.server.fastmcp import FastMCP, Context

# --- Constants ---
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_API_KEY = "ollama"  # Placeholder
OLLAMA_MODEL = "phi3"
BOT_NAME = "BotA"
SYSTEM_PROMPT = (
    "You are BotA, a professional developer discussing a new project with BotB. "
    "Your goal is to collaborate effectively. Keep your replies concise and brief."
)
HOST_IP = "127.0.0.1"
PORT = 8001
# --- End Constants ---

# Configure logging to file
LOG_APP_PATH = "app.log" # Log file in the same directory
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File Handler
file_handler = logging.FileHandler(LOG_APP_PATH, mode='a', encoding='utf-8')
file_handler.setFormatter(log_formatter)

# Configure root logger to use ONLY the file handler
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
root_logger.addHandler(file_handler)
root_logger.setLevel(logging.INFO)

# Get logger for this specific module
logger = logging.getLogger(BOT_NAME)

# Instantiate the client for Ollama
client = AsyncOpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key=OLLAMA_API_KEY
)

# Create the MCP server
mcp = FastMCP(BOT_NAME)

@mcp.tool()
async def chat(ctx: Context, message: str, history: list[dict]) -> types.CallToolResult:
    """
    Handles chat requests.

    Prepends the system prompt to the history + message,
    calls the Ollama LLM, and returns the reply or error as a CallToolResult.
    """
    logger.info(f"Received chat message: '{message[:50]}...'")
    msgs = history + [{"role": "user", "content": message}]
    msgs.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    try:
        resp = await client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=msgs
        )
        reply = resp.choices[0].message.content
        logger.info(f"Generated reply: '{reply[:50]}...'")
        # Return success result
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=reply)]
        )
    except APIError as e:
        logger.error(f"Ollama API error: {e}", exc_info=True)
        # Return error result
        return types.CallToolResult(
            isError=True,
            content=[types.TextContent(type="text", text=f"Ollama API error: {str(e)}")]
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat tool: {e}", exc_info=True)
        # Return error result
        return types.CallToolResult(
            isError=True,
            content=[types.TextContent(type="text", text=f"An unexpected error occurred in {BOT_NAME}: {str(e)}")]
        )

if __name__ == "__main__":
    logger.info(f"Starting {BOT_NAME} server on {HOST_IP}:{PORT}")
    app = FastAPI(title=BOT_NAME)
    app.mount("/", mcp.sse_app())
    uvicorn.run(app, host=HOST_IP, port=PORT)
