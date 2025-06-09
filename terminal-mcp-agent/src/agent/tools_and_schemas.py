from typing import Optional, List
from pydantic import BaseModel, Field

# --- Filesystem Tool Schemas ---

class ListFilesTool(BaseModel):
    """Lists files and directories in a specified path."""
    path: Optional[str] = Field(
        default=".",
        description="The directory path to list files from. Defaults to the current directory."
    )

class ReadFileTool(BaseModel):
    """Reads the content of a specified file."""
    path: str = Field(description="The path to the file to be read.")

class CreateDirectoryTool(BaseModel):
    """Creates a new directory at the specified path."""
    path: str = Field(description="The full path where the new directory should be created.")

# --- Generic Parsed Command Schema ---

class ParsedCommand(BaseModel):
    """Represents a command parsed by the LLM, ready for execution."""
    tool_name: str = Field(description="The name of the MCP tool to be executed (e.g., 'ListFilesTool').")
    args: dict = Field(description="A dictionary of arguments for the tool, matching its schema.")

# --- GUI Automation Tool Schemas (Placeholder for now, as per plan) ---
# We will define these in more detail when implementing F3.

# class MoveMouseTool(BaseModel):
#     x: int
#     y: int

# class ClickTool(BaseModel):
#     x: int
#     y: int
#     button: Optional[str] = "left"

# class TypeTextTool(BaseModel):
#     text: str
