import os
from dotenv import load_dotenv
from typing import Union

from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI

from .state import AgentState
from .configuration import Configuration # Will be used for model config
from .prompts import COMMAND_PARSER_INSTRUCTIONS, get_current_date
from .tools_and_schemas import (
    ListFilesTool,
    ReadFileTool,
    CreateDirectoryTool,
    ParsedCommand # Using this generic schema for now for the output of parser
)

# Load environment variables from .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in the environment or .env file")

# --- Node Definitions ---

def parse_user_command(state: AgentState, config: RunnableConfig) -> dict:
    """
    Parses the user's natural language command into a structured MCP tool call
    using Gemini with structured output.
    """
    print(f"--- Debug: Entering parse_user_command ---")
    print(f"--- Debug: User command: {state['user_command']} ---")

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
        print(f"--- Debug: LLM raw parsed_result: {parsed_result} ---")
        if isinstance(parsed_result, ParsedCommand) and parsed_result.tool_name != "NoSuitableToolFound":
            # TODO: Validate that parsed_result.tool_name is one of our actual tool classes
            # and that parsed_result.args match the schema of that tool.
            # For now, we assume the LLM gets it right based on the prompt.
            return {
                "parsed_command": {"tool_name": parsed_result.tool_name, "args": parsed_result.args},
                "error_message": None
            }
        else:
            error_msg = f"No suitable tool found or LLM failed to identify one for command: {state['user_command']}"
            if isinstance(parsed_result, ParsedCommand) and parsed_result.args:
                 error_msg = f"No suitable tool found for command: {parsed_result.args.get('original_command', state['user_command'])}"
            print(f"--- Debug: {error_msg} ---")
            return {"parsed_command": None, "error_message": error_msg}
    except Exception as e:
        print(f"--- Debug: Exception during LLM invocation or parsing: {e} ---")
        return {"parsed_command": None, "error_message": f"Error parsing command: {str(e)}"}

def execute_mcp_tool(state: AgentState, config: RunnableConfig) -> dict:
    """
    Executes the parsed MCP tool.
    Placeholder: For now, it just logs the command and returns a mock success.
    Actual tool execution will be implemented later with MCP server classes.
    """
    print(f"--- Debug: Entering execute_mcp_tool ---")
    parsed_command = state.get('parsed_command')
    if not parsed_command:
        return {"tool_output": None, "error_message": "No command was parsed for execution."}

    tool_name = parsed_command.get('tool_name')
    args = parsed_command.get('args', {})

    print(f"--- Debug: Attempting to execute tool: {tool_name} with args: {args} ---")

    # Mock execution for now
    # In the future, this will dispatch to actual tool implementations (e.g., FilesystemMCPServer.list_files(args))
    if tool_name == ListFilesTool.__name__:
        output = f"Mock success: '{tool_name}' called with path '{args.get('path', '.')}'"
    elif tool_name == ReadFileTool.__name__:
        output = f"Mock success: '{tool_name}' called to read file '{args.get('path')}'"
    elif tool_name == CreateDirectoryTool.__name__:
        output = f"Mock success: '{tool_name}' called to create directory '{args.get('path')}'"
    else:
        print(f"--- Debug: Unknown tool_name: {tool_name} ---")
        return {"tool_output": None, "error_message": f"Unknown tool: {tool_name}"}

    print(f"--- Debug: Mock tool output: {output} ---")
    return {"tool_output": output, "error_message": None}

def format_tool_output(state: AgentState, config: RunnableConfig) -> dict:
    """
    Formats the tool's output for display.
    Placeholder: For now, it's a simple pass-through or basic formatting.
    """
    print(f"--- Debug: Entering format_tool_output ---")
    if state.get('error_message'):
        # If there's an error message, that should be the primary output to the user
        final_output = f"Error: {state['error_message']}"
        print(f"--- Debug: Formatting error message: {final_output} ---")
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

    print(f"--- Debug: Formatted output: {final_output} ---")
    # Reset state for next command
    return {"tool_output": final_output, "parsed_command": None, "user_command": None}


# --- Conditional Edge Logic ---

def should_execute_tool(state: AgentState) -> str:
    """Determines if a command was successfully parsed and is ready for execution."""
    print(f"--- Debug: Entering should_execute_tool ---")
    if state.get('error_message'):
        print(f"--- Debug: Error detected, routing to format_tool_output ---")
        return "format_tool_output" # Route to format output to show the error
    if state.get('parsed_command') and state['parsed_command'].get('tool_name') != "NoSuitableToolFound":
        print(f"--- Debug: Command parsed, routing to execute_mcp_tool ---")
        return "execute_mcp_tool"
    print(f"--- Debug: No suitable tool or error in parsing, routing to format_tool_output ---")
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
    print("Testing agent graph directly (mock execution)...")

    # Load configuration for the test
    test_config = RunnableConfig(configurable={"query_generator_model": "gemini-pro"}) # Example model

    # Example 1: List files
    inputs1 = AgentState(user_command="list files in my_documents")
    print(f"\nInvoking graph with: {inputs1}")
    for event in agent_graph.stream(inputs1, config=test_config):
        print(f"Event: {event}")

    # Example 2: Read a file
    inputs2 = AgentState(user_command="cat /etc/passwd")
    print(f"\nInvoking graph with: {inputs2}")
    for event in agent_graph.stream(inputs2, config=test_config):
        print(f"Event: {event}")

    # Example 3: Unknown command
    inputs3 = AgentState(user_command="what's the weather like?")
    print(f"\nInvoking graph with: {inputs3}")
    for event in agent_graph.stream(inputs3, config=test_config):
        print(f"Event: {event}")

    # Example 4: Command that might cause parsing error (if LLM struggles)
    # inputs4 = AgentState(user_command="!@#$%^&*()")
    # print(f"\nInvoking graph with: {inputs4}")
    # for event in agent_graph.stream(inputs4, config=test_config):
    #     print(f"Event: {event}")

    print("\nGraph testing complete.")
