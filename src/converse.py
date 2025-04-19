"""Drives a conversation between BotA and BotB using MCP clients."""

import asyncio
import datetime
import json
import logging
from typing import TextIO # For log_file type hint

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import CallToolResult, TextContent

# --- Constants ---
URL_A = "http://127.0.0.1:8001/sse"
URL_B = "http://127.0.0.1:8002/sse"
LOG_FILE_PATH = "conversation_log.txt"
INITIAL_MESSAGE = "Hello, BotB! let's discuss on llm and ai"
MAX_TURNS = 500
TURN_DELAY_SECONDS = 10
# --- End Constants ---

# --- ANSI Color Codes ---
COLOR_BLUE = "\033[94m"
COLOR_GREEN = "\033[92m"
COLOR_RESET = "\033[0m"
# --- End Color Codes ---

# Configure logging to file
LOG_APP_PATH = "app.log" # Log file in the same directory
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File Handler
file_handler = logging.FileHandler(LOG_APP_PATH, mode='a', encoding='utf-8')
file_handler.setFormatter(log_formatter)

# Configure root logger to use ONLY the file handler
# This prevents libraries like httpx, mcp from logging to console by default
root_logger = logging.getLogger()
# Remove existing handlers (like the default StreamHandler)
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
root_logger.addHandler(file_handler)
root_logger.setLevel(logging.INFO) # Set level for root logger

# Get logger for this specific module
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherits level from root

# Optionally set lower levels for verbose libraries if needed for the file log
# logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("mcp").setLevel(logging.WARNING)


async def extract_reply(res: CallToolResult) -> str:
    """Extracts the string reply from a CallToolResult, raising on error."""
    if res.isError:
        error_message = "Unknown error"
        if isinstance(res.content, list) and res.content:
            first_item = res.content[0]
            if isinstance(first_item, TextContent):
                # Error message is in the text field - no need to parse JSON here typically
                error_message = first_item.text
            elif isinstance(first_item, str):
                 error_message = first_item
        logger.error(f"Tool call error: {error_message}")
        raise RuntimeError(f"Tool call failed: {error_message}")

    # --- Reinstate JSON parsing workaround for success path --- 
    if isinstance(res.content, list) and res.content and isinstance(res.content[0], TextContent):
        potential_json_string = res.content[0].text
        try:
            # Attempt to parse the text field as JSON
            parsed_data = json.loads(potential_json_string)
            # Extract the actual text from the nested structure
            if isinstance(parsed_data, dict) and 'content' in parsed_data and isinstance(parsed_data['content'], list) and parsed_data['content']:
                 nested_content = parsed_data['content'][0]
                 if isinstance(nested_content, dict) and 'text' in nested_content:
                      actual_text = nested_content['text']
                      # print(f"DEBUG: Parsed nested text: {repr(actual_text)}") # Keep inner DEBUG for now
                      return actual_text
            # If parsing succeeded but structure is wrong, or if it wasn't JSON, treat original string as the text
            # print(f"DEBUG: Failed to parse nested structure or unexpected format in {repr(potential_json_string)}, returning as is.") # Keep inner DEBUG for now
            return potential_json_string
        except json.JSONDecodeError:
            # If it's not JSON, assume it's the actual text
            # print(f"DEBUG: Not JSON, returning as is: {repr(potential_json_string)}") # Keep inner DEBUG for now
            return potential_json_string
        except Exception as e:
             logger.error(f"Error during nested parsing: {e}", exc_info=True)
             raise TypeError(f"Failed during nested parsing of: {potential_json_string}") from e
    else:
        # Handle unexpected success format
        content_repr = repr(res.content)
        logger.error(f"Unexpected success result format: {content_repr}")
        raise TypeError(f"Expected list with TextContent in content, got {type(res.content)}")


async def main() -> None:
    """Runs the main conversation loop between BotA and BotB."""
    logger.info(f"Connecting to BotA ({URL_A}) and BotB ({URL_B})")

    # nest your contexts so cleanup is well-scoped
    try:
        async with sse_client(URL_A) as (r_a, w_a), \
                   sse_client(URL_B) as (r_b, w_b), \
                   ClientSession(r_a, w_a) as client_a, \
                   ClientSession(r_b, w_b) as client_b:

            await client_a.initialize()
            await client_b.initialize()
            logger.info("MCP clients initialized.")

            history_a: list[dict] = []
            history_b: list[dict] = []
            message: str = INITIAL_MESSAGE

            logger.info(f"Starting conversation log: {LOG_FILE_PATH}")
            print(f"{COLOR_GREEN}--- Starting Conversation ---{COLOR_RESET}") # Add start message
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n--- New Conversation Started: {datetime.datetime.now()} ---\n")
                
                for turn in range(MAX_TURNS):
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    logger.info(f"Starting Turn {turn + 1}")
                    log_file.write(f"\n[Turn {turn + 1} - {timestamp}]\n")
                    
                    # --- BotB Turn --- 
                    logger.debug(f"Sending to BotB: '{message[:50]}...'")
                    log_file.write(f"Driver -> BotB: {message}\n")
                    history_b.append({"role": "user", "content": message}) # Add user msg *before* call
                    res_b = await client_b.call_tool("chat", {
                        "message": message,      # Send current message
                        "history": history_b[:-1] # Send history *excluding* current user msg
                    })
                    reply_b = await extract_reply(res_b)
                    history_b.append({"role": "assistant", "content": reply_b}) # Add assistant reply *after* call
                    # Use color for printing
                    print(f"{COLOR_BLUE}BotB ➔{COLOR_RESET} {reply_b}") 
                    log_file.write(f"BotB -> Driver: {reply_b}\n")

                    # --- BotA Turn --- 
                    logger.debug(f"Sending to BotA: '{reply_b[:50]}...'")
                    log_file.write(f"Driver -> BotA: {reply_b}\n")
                    history_a.append({"role": "user", "content": reply_b}) # Add user msg *before* call
                    res_a = await client_a.call_tool("chat", {
                        "message": reply_b,      # Send BotB's reply as the message
                        "history": history_a[:-1] # Send history *excluding* current user msg
                    })
                    reply_a = await extract_reply(res_a)
                    history_a.append({"role": "assistant", "content": reply_a}) # Add assistant reply *after* call
                    # Use color for printing
                    print(f"{COLOR_GREEN}BotA ➔{COLOR_RESET} {reply_a}") 
                    log_file.write(f"BotA -> Driver: {reply_a}\n")

                    message = reply_a # Set up message for next turn (to BotB)
                    
                    logger.debug(f"Pausing for {TURN_DELAY_SECONDS} seconds...")
                    # await asyncio.sleep(TURN_DELAY_SECONDS)
                    
            print(f"{COLOR_GREEN}--- Conversation Ended ---{COLOR_RESET}") # Add end message
                    
    except ConnectionRefusedError as e:
        logger.error(f"Connection failed: Could not connect to bots. Ensure BotA/BotB servers are running. Details: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
