"""LangGraph workflow for the Terminal MCP agent."""

import logging
import os

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from .configuration import Configuration  # Will be used for model config
from .prompts import COMMAND_PARSER_INSTRUCTIONS, get_current_date
from .state import AgentState
from .tools_and_schemas import (
    CreateDirectoryTool,
    ListFilesTool,
    ParsedCommand,  # Using this generic schema for now for the output of parser
    ReadFileTool,
)

# Load environment variables from .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in the environment or .env file")

logger = logging.getLogger(__name__)

# --- Node Definitions ---

def parse_user_command(state: AgentState, config: RunnableConfig) -> dict:
    """Parse the user's command using Gemini and return a structured tool call."""
    logger.debug("Entering parse_user_command")
    logger.debug("User command: %s", state['user_command'])

    app_config = Configuration.from_runnable_config(config)
    llm = ChatGoogleGenerativeAI(
        model=app_config.query_generator_model, # Using query_generator_model for now
        temperature=0.1, # Low temperature for more deterministic parsing
        api_key=GEMINI_API_KEY
    )

    # For structured output, we tell the LLM which Pydantic model to use for its response.
    # We want it to fill our ParsedCommand schema.
    structured_llm = llm.with_structured_output(ParsedCommand)

    prompt = COMMAND_PARSER_INSTRUCTIONS.format(
        current_date=get_current_date(),
        user_command=state['user_command']
    )

    try:
        parsed_result = structured_llm.invoke(prompt)
        logger.debug("LLM raw parsed_result: %s", parsed_result)
        if not isinstance(parsed_result, ParsedCommand):
            raise ValueError("LLM did not return ParsedCommand")
        if parsed_result.tool_name == "NoSuitableToolFound":
            error_msg = (
                f"No suitable tool found for command: "
                f"{parsed_result.args.get('original_command', state['user_command'])}"
            )
            logger.debug(error_msg)
            return {"parsed_command": None, "error_message": error_msg}

        tool_map = {
            ListFilesTool.__name__: ListFilesTool,
            ReadFileTool.__name__: ReadFileTool,
            CreateDirectoryTool.__name__: CreateDirectoryTool,
        }
        tool_class = tool_map.get(parsed_result.tool_name)
        if tool_class is None:
            error_msg = f"Unknown tool: {parsed_result.tool_name}"
            logger.error(error_msg)
            return {"parsed_command": None, "error_message": error_msg}

        try:
            validated = tool_class(**parsed_result.args)
        except ValidationError as e:
            error_msg = f"Invalid arguments for {parsed_result.tool_name}: {e}"
            logger.error(error_msg)
            return {"parsed_command": None, "error_message": error_msg}

        return {
            "parsed_command": {
                "tool_name": parsed_result.tool_name,
                "args": validated.model_dump() if hasattr(validated, "model_dump") else validated.dict(),
            },
            "error_message": None,
        }
    except Exception as e:
        logger.exception("Exception during LLM invocation or parsing: %s", e)
        return {"parsed_command": None, "error_message": f"Error parsing command: {str(e)}"}

def execute_mcp_tool(state: AgentState, config: RunnableConfig) -> dict:
    """Execute the parsed MCP tool.

    Placeholder: For now, it just logs the command and returns a mock success.
    Actual tool execution will be implemented later with MCP server classes.
    """
    logger.debug("Entering execute_mcp_tool")
    parsed_command = state.get('parsed_command')
    if not parsed_command:
        return {"tool_output": None, "error_message": "No command was parsed for execution."}

    tool_name = parsed_command.get('tool_name')
    args = parsed_command.get('args', {})

    logger.debug("Attempting to execute tool: %s with args: %s", tool_name, args)

    # Mock execution for now
    # In the future, this will dispatch to actual tool implementations (e.g., FilesystemMCPServer.list_files(args))
    if tool_name == ListFilesTool.__name__:
        output = f"Mock success: '{tool_name}' called with path '{args.get('path', '.')}'"
    elif tool_name == ReadFileTool.__name__:
        output = f"Mock success: '{tool_name}' called to read file '{args.get('path')}'"
    elif tool_name == CreateDirectoryTool.__name__:
        output = f"Mock success: '{tool_name}' called to create directory '{args.get('path')}'"
    else:
        logger.error("Unknown tool_name: %s", tool_name)
        return {"tool_output": None, "error_message": f"Unknown tool: {tool_name}"}

    logger.debug("Mock tool output: %s", output)
    return {"tool_output": output, "error_message": None}

def format_tool_output(state: AgentState, config: RunnableConfig) -> dict:
    """Format the tool's output for display.

    Placeholder: For now, it's a simple pass-through or basic formatting.
    """
    logger.debug("Entering format_tool_output")
    if state.get('error_message'):
        # If there's an error message, that should be the primary output to the user
        final_output = f"Error: {state['error_message']}"
        logger.debug("Formatting error message: %s", final_output)
        # Clear error after displaying, or decide on error handling flow
        return {"tool_output": final_output, "error_message": None, "parsed_command": None, "user_command": None}

    tool_output = state.get('tool_output')
    if tool_output is None:
        final_output = "No output from tool or an earlier error occurred."
    elif isinstance(tool_output, str):
        final_output = tool_output
    else:
        # Basic formatting for non-string outputs (e.g., lists, dicts)
        import json
        try:
            final_output = json.dumps(tool_output, indent=2)
        except TypeError:
            final_output = str(tool_output)

    logger.debug("Formatted output: %s", final_output)
    # Reset state for next command
    return {"tool_output": final_output, "parsed_command": None, "user_command": None}


# --- Conditional Edge Logic ---

def should_execute_tool(state: AgentState) -> str:
    """Return the next node based on parsing results."""
    logger.debug("Entering should_execute_tool")
    if state.get('error_message'):
        logger.debug("Error detected, routing to format_tool_output")
        return "format_tool_output" # Route to format output to show the error
    if state.get('parsed_command') and state['parsed_command'].get('tool_name') != "NoSuitableToolFound":
        logger.debug("Command parsed, routing to execute_mcp_tool")
        return "execute_mcp_tool"
    logger.debug("No suitable tool or error in parsing, routing to format_tool_output")
    # If no tool found or other parsing issue not caught as an error yet
    return "format_tool_output"

# --- Graph Definition ---

builder = StateGraph(AgentState)

builder.add_node("parse_user_command", parse_user_command)
builder.add_node("execute_mcp_tool", execute_mcp_tool)
builder.add_node("format_tool_output", format_tool_output)

builder.add_edge(START, "parse_user_command")

builder.add_conditional_edges(
    "parse_user_command",
    should_execute_tool,
    {
        "execute_mcp_tool": "execute_mcp_tool",
        "format_tool_output": "format_tool_output" # To handle parsing errors or NoSuitableToolFound
    }
)

builder.add_edge("execute_mcp_tool", "format_tool_output")
builder.add_edge("format_tool_output", END) # End of a single command processing cycle

# Compile the graph
agent_graph = builder.compile()

# --- Test Invocation (Optional, for quick testing if run directly) ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Testing agent graph directly (mock execution)...")

    # Load configuration for the test
    test_config = RunnableConfig(configurable={"query_generator_model": "gemini-pro"}) # Example model

    # Example 1: List files
    inputs1 = AgentState(user_command="list files in my_documents")
    logger.info("\nInvoking graph with: %s", inputs1)
    for event in agent_graph.stream(inputs1, config=test_config):
        logger.info("Event: %s", event)

    # Example 2: Read a file
    inputs2 = AgentState(user_command="cat /etc/passwd")
    logger.info("\nInvoking graph with: %s", inputs2)
    for event in agent_graph.stream(inputs2, config=test_config):
        logger.info("Event: %s", event)

    # Example 3: Unknown command
    inputs3 = AgentState(user_command="what's the weather like?")
    logger.info("\nInvoking graph with: %s", inputs3)
    for event in agent_graph.stream(inputs3, config=test_config):
        logger.info("Event: %s", event)

    # Example 4: Command that might cause parsing error (if LLM struggles)
    # inputs4 = AgentState(user_command="!@#$%^&*()")
    # logger.info("\nInvoking graph with: %s", inputs4)
    # for event in agent_graph.stream(inputs4, config=test_config):
    #     logger.info("Event: %s", event)

    logger.info("\nGraph testing complete.")
