from typing import TypedDict, Optional, List, Any
from langgraph.graph import add_messages
from typing_extensions import Annotated

class AgentState(TypedDict):
    """
    Represents the state of the Terminal MCP Agent.
    """
    # The initial natural language command from the user
    user_command: str

    # The parsed command, including the tool to be called and its arguments
    # Example: {"tool_name": "list_files", "args": {"path": "./docs"}}
    parsed_command: Optional[dict] = None

    # The output from the executed MCP tool
    tool_output: Optional[Any] = None

    # Any error message encountered during processing
    error_message: Optional[str] = None

    # Conversation history (for potential future use, like context-aware commands)
    # messages: Annotated[List, add_messages]
