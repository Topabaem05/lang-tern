import os
import sys # Added for sys.exit()
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig

# Attempt to import graph and states from the current package
try:
    from .graph import graph
    from .state import OverallState
except ImportError:
    # Fallback for cases where the script might be run directly
    # and Python doesn't recognize the current directory as part of a package
    from graph import graph
    from state import OverallState

from typing import List, Dict, Any

def display_sources(sources: List[Dict[str, Any]]):
    """Displays the gathered sources in a readable format."""
    if not sources:
        print("\nNo sources gathered for this response.")
        return
    print("\nSources:")
    for i, source in enumerate(sources):
        label = source.get('label', 'N/A')
        url = source.get('value', 'N/A') # 'value' holds the original URL
        # short_url = source.get('short_url', 'N/A') # short_url is used internally
        print(f"  {i+1}. [{label}]: {url}")

def main():
    """Main function to run the terminal-based chat agent."""
    load_dotenv()

    # Check for Gemini API Key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please set it in your .env file or environment.")
        return
    if gemini_api_key == "YOUR_API_KEY_HERE" or gemini_api_key == "YOUR_GEMINI_API_KEY_HERE":
        print("Warning: The GEMINI_API_KEY is still set to the placeholder value.")
        print("The agent will likely fail when trying to contact Google services.")
        print("Please update it in your .env file with a real API key for full functionality.")

    chat_history: List[BaseMessage] = []

    # --- Automated Test Run ---
    print("--- Running Automated Test ---")
    test_question = "What is Gemini AI?"
    print(f"Test Question: {test_question}")

    test_human_message = HumanMessage(content=test_question)
    current_chat_history_for_test = list(chat_history) # Should be empty at start
    current_chat_history_for_test.append(test_human_message)

    test_initial_state: OverallState = {
        "messages": [test_human_message],
        "chat_history": current_chat_history_for_test,
        "search_query": [],
        "web_research_result": [],
        "sources_gathered": [],
        "initial_search_query_count": 1,
        "max_research_loops": 2, # Reduced for quick test
        "reasoning_model": "gemini-1.5-flash-latest",
    }
    test_config = RunnableConfig(configurable={"recursion_limit": 25}) # Reduced for quick test

    print("Agent (Test) is thinking...")
    try:
        final_test_state = graph.invoke(test_initial_state, config=test_config)

        if final_test_state and final_test_state.get('messages'):
            ai_message_obj = final_test_state['messages'][-1]
            if isinstance(ai_message_obj, AIMessage):
                print(f"\nAgent (Test Response): {ai_message_obj.content}")
                # chat_history.append(ai_message_obj) # Not adding to main history for this auto-test
            else:
                print(f"\nAgent (Test Response): Unexpected message type: {type(ai_message_obj)}")
                print(f"Content: {ai_message_obj.content if hasattr(ai_message_obj, 'content') else 'N/A'}")

            if 'sources_gathered' in final_test_state:
                display_sources(final_test_state['sources_gathered'])
        else:
            print("Agent (Test) did not return a message.")

    except Exception as e:
        print(f"\nError during agent (Test) execution: {e}")

    print("--- Automated Test Finished ---")
    print("Exiting after automated test as per subtask requirement.")
    sys.exit(0)

    # --- Interactive Loop ---
    print("\nStarting interactive session...")
    print("Terminal Agent started. Type 'exit' or 'quit' to end.")
    # chat_history is already initialized, it will be empty if test didn't modify it,
    # or could carry over if we decided to let the test run modify the main history.
    # For now, test run does not modify the main chat_history.

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting agent...")
            break

        if not user_input.strip():
            continue

        human_message = HumanMessage(content=user_input)
        chat_history.append(human_message)

        initial_state: OverallState = {
            "messages": [human_message],
            "chat_history": list(chat_history),
            "search_query": [],
            "web_research_result": [],
            "sources_gathered": [],
            "initial_search_query_count": 1,
            "max_research_loops": 3,
            "reasoning_model": "gemini-1.5-flash-latest",
        }
        config = RunnableConfig(configurable={"recursion_limit": 50})

        print("Agent is thinking...")
        try:
            final_state = graph.invoke(initial_state, config=config)

            if final_state and final_state.get('messages'):
                ai_message_obj = final_state['messages'][-1]
                if isinstance(ai_message_obj, AIMessage):
                    print(f"\nAgent: {ai_message_obj.content}")
                    chat_history.append(ai_message_obj)
                else:
                    print(f"\nAgent: Received an unexpected message type: {type(ai_message_obj)}")
                    print(f"Content: {ai_message_obj.content if hasattr(ai_message_obj, 'content') else 'N/A'}")

                if 'sources_gathered' in final_state:
                    display_sources(final_state['sources_gathered'])
                else:
                    print("No sources information in final state.")
            else:
                print("Agent did not return a message.")
        except Exception as e:
            print(f"\nError during agent execution: {e}")


if __name__ == "__main__":
    main()
