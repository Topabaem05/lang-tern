# Terminal MCP Agent

## Project Overview

The Terminal MCP Agent is a command-line interface (CLI) application designed to provide a sophisticated conversational AI experience. It leverages Google's Gemini large language models and the LangGraph framework to understand user queries, perform web research when necessary, and deliver informative, cited answers directly in your terminal.

## Features Detailed

-   **Conversational AI**: Engage in natural, multi-turn conversations. The agent maintains a chat history to understand context and provide relevant follow-up responses.
-   **Dynamic Web Search**: When questions require up-to-date information or knowledge beyond its training data, the agent automatically:
    -   Generates optimized search queries based on the conversation.
    -   Utilizes Google Search (via the Gemini API's built-in function calling) to find relevant web pages.
    -   Summarizes the findings from web research.
-   **Cited Answers**: Key information in the agent's responses is backed by citations. After each answer, a list of sources used is provided, including the title and original URL, allowing for verification.
-   **Contextual Understanding**: By maintaining and referencing the conversation history, the agent can handle follow-up questions and nuanced queries more effectively.
-   **Configurable Behavior**: Key aspects like the number of initial search queries and maximum research loops can be configured within the agent's code.

## Architecture Overview

The agent's logic is orchestrated by LangGraph, a library for building stateful, multi-actor applications with LLMs. The core flow involves several interconnected nodes:

1.  **Query Generation**: The user's input (and conversation history) is analyzed to formulate effective search queries if external information is needed.
2.  **Web Search**: The generated queries are executed using the Google Search tool available through the Gemini API.
3.  **Reflection**: The search results are assessed to determine if they are sufficient to answer the user's question or if further research or clarification is needed (potentially generating follow-up queries).
4.  **Answer Finalization**: A comprehensive answer is synthesized from the gathered information (both from its internal knowledge and web research). Citations from web sources are embedded into the answer, and full URLs are provided.

This cyclical process allows the agent to iteratively refine its understanding and search strategy to provide the best possible answer.

## Prerequisites

-   Python 3.10+
-   Git

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    # Replace <repository_url> with the actual URL of your repository
    git clone <repository_url>
    cd terminal-mcp-agent
    ```

2.  **Create a Python virtual environment (recommended):**
    This isolates the project's dependencies from your global Python setup.
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On macOS/Linux
    # For Windows (cmd.exe): .venv\Scripts\activate.bat
    # For Windows (PowerShell): .venv\Scripts\Activate.ps1
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your API Key:**
    -   This project requires a Google Gemini API Key. You can obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).
    -   Make a copy of the example environment file:
        ```bash
        cp .env.example .env
        ```
    -   Open the newly created `.env` file in a text editor.
    -   Replace `"YOUR_GEMINI_API_KEY_HERE"` with your actual Gemini API key.
        ```env
        # Example content for .env file
        GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
        ```
    -   Save the `.env` file. This file is listed in `.gitignore`, so your API key will not be accidentally committed to the repository.

## Usage

1.  **Run the Agent:**
    Ensure your virtual environment is activated and you are in the `terminal-mcp-agent` directory.
    ```bash
    python -m src.agent.app
    ```
    The script includes an automated test run with a predefined question ("What is Gemini AI?"). It will print the test results (which may show an API error if your key is invalid) and then exit. To use interactively, you'll need to comment out or remove the `sys.exit(0)` line at the end of the automated test block in `src/agent/app.py`.

2.  **Interact with the Agent (after modifying `app.py` for interactive use):**
    -   Once the agent starts and the automated test (if enabled) completes, you will see a prompt:
        ```
        You:
        ```
    -   Type your question and press Enter.
    -   The agent will print "Agent is thinking..." while processing.
    -   The agent's answer will be displayed, followed by a list of sources if web research was performed.
        ```
        Agent: [The agent's response to your query...]

        Sources:
          1. [Source Title 1]: https://example.com/source1
          2. [Source Title 2]: https://example.com/source2
        ```

3.  **End the Session:**
    Type `exit` or `quit` at the prompt and press Enter.

## Troubleshooting

-   **`ValueError: GEMINI_API_KEY is not set`**:
    This means the `GEMINI_API_KEY` was not found in your environment.
    -   Ensure you have created a `.env` file in the `terminal-mcp-agent` directory.
    -   Verify that the `.env` file contains the line `GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"` with your real key.
    -   Make sure you are running the application from the `terminal-mcp-agent` directory.

-   **`400 API key not valid` (or similar API errors)**:
    This error is returned from the Google Gemini API.
    -   Double-check that the `GEMINI_API_KEY` in your `.env` file is correct and valid.
    -   Ensure your Google Cloud project associated with the API key has the "Generative Language API" (or "AI Platform" or similar, depending on the exact service) enabled.
    -   Check if your API key has any restrictions (e.g., IP address restrictions) that might prevent it from being used in your current environment.

-   **`ModuleNotFoundError: No module named 'some_module'`**:
    -   Ensure your virtual environment is activated.
    -   Try reinstalling dependencies: `pip install -r requirements.txt`.

-   **Issues with Relative Imports during Development**:
    If you encounter `ImportError: attempted relative import with no known parent package` when running scripts directly (e.g., `python src/agent/app.py`), use the `python -m` flag to run as a module, as shown in the "Usage" section: `python -m src.agent.app`. This helps Python correctly resolve package paths.

## Future Improvements (Optional)

-   Integration with more diverse tools (e.g., local file access, code execution).
-   More sophisticated state management for complex tasks.
-   Ability to configure agent parameters (like model choice) via command-line arguments or a configuration file.
-   Streaming output for a more responsive feel during generation.
-   Enhanced error handling and recovery.

This README should provide a good starting point for users.
