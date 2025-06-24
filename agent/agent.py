# agent.py
import json
import os
import logging # Added logging
from typing import Callable, List
from anthropic import Anthropic, APIError # Added APIError
from dotenv import load_dotenv

load_dotenv()

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ToolDefinition:
    def __init__(self, name: str, description: str, input_schema, func: Callable[[dict], str]):
        self.name = name
        self.description = description
        self.input_schema = input_schema  # This is typically a Pydantic model for schema generation
        self.func = func

    def execute(self, input_data: dict) -> str:
        # The actual validation of input_data against input_schema (if it's a Pydantic model)
        # is typically handled by the Pydantic model itself when the tool's `func` is called,
        # often via `ToolModel(**input_data)`.
        # This Agent class forwards the input_data as received from Anthropic.
        return self.func(input_data)

class Agent:
    def __init__(self, get_user_message: Callable[[], str], tools: List[ToolDefinition]):
        self.get_user_message = get_user_message
        self.tools = {tool.name: tool for tool in tools}
        self.conversation = [] # Initialize conversation history here
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def anthropic_tools(self):
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema.schema() if hasattr(tool.input_schema, 'schema') else {},
            }
            for tool in self.tools.values()
        ]

    def run(self):
        print("Chat with Claude (Ctrl-C to quit)")
        read_user_input = True # Start by reading user input

        while True:
            if read_user_input:
                user_input = self.get_user_message()
                if user_input is None:  # Typically from Ctrl-C or EOF
                    logging.info("User input is None. Exiting agent run loop.")
                    break
                # Append user's message to the conversation history
                self.conversation.append({"role": "user", "content": user_input})
                logging.info("Appended user message to conversation.")

            # Send conversation to Anthropic
            try:
                logging.info("Sending message to Anthropic API.")
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=2048,
                    messages=self.conversation,
                    tools=self.anthropic_tools(),
                )
            except APIError as e:
                logging.error(f"Anthropic API error: {e}")
                print(f"An API error occurred: {e}. Please check your connection or API key.")
                # Allowing continuation, maybe it's a temporary issue.
                # Depending on the error type, one might want to break.
                # For now, we'll let it try to get user input again if read_user_input is true,
                # or it might retry if it was a tool response cycle.
                # This could lead to retrying the same API call if read_user_input is false.
                # A more robust solution might involve specific retry logic here.
                # For now, if it's a persistent API error, the user can Ctrl-C.
                # Let's ensure the user gets a chance to respond or the loop breaks.
                read_user_input = True # Force user input next to avoid loops on API errors during tool processing
                continue # Skip the rest of this iteration
            except Exception as e:
                logging.exception("An unexpected error occurred during Anthropic API call.") # Logs stack trace
                print(f"An unexpected error occurred: {e}")
                break # For unexpected errors, it's safer to break

            # --- Response Processing ---
            self._append_assistant_message_to_conversation(response)

            tool_results, has_tool_use = self._process_assistant_response_content()

            if has_tool_use:
                self._append_tool_results_to_conversation(tool_results)
                read_user_input = False # Claude will process the tool results and respond.
            else:
                # If Claude just talked (no tool use), it's the user's turn to talk next.
                read_user_input = True

    def _append_assistant_message_to_conversation(self, response):
        """Appends the assistant's raw response content to the conversation history."""
        # The assistant's response (raw API response.content) must be added to the conversation.
        # response.content is a list of content blocks (e.g., text, tool_use).
        if response.content:
            self.conversation.append({
                "role": "assistant",
                "content": response.content  # This is already a list of content blocks
            })
        else:
            # This case should ideally not happen with a successful API call
            # If it does, append an empty content list for the assistant.
            logging.warning("Anthropic API response content was empty.")
            self.conversation.append({
                "role": "assistant",
                "content": []
            })
        logging.info("Appended assistant message to conversation.")


    def _process_assistant_response_content(self):
        """
        Processes the latest assistant message in the conversation for text and tool uses.
        Executes tools if any are found.
        Returns a tuple: (list of tool results, boolean indicating if any tool was used).
        """
        tool_results_for_next_turn = []
        has_tool_use_in_response = False

        # Ensure we are looking at the last assistant message's content
        if not self.conversation or self.conversation[-1]["role"] != "assistant":
            logging.error("Cannot process assistant response: No assistant message found at the end of the conversation.")
            return [], False # Should not happen if _append_assistant_message_to_conversation was called

        last_assistant_message_content = self.conversation[-1]["content"]

        # Ensure last_assistant_message_content is iterable (it should be a list of ContentBlock objects)
        if not isinstance(last_assistant_message_content, list):
            logging.error(f"last_assistant_message_content is not a list as expected: {type(last_assistant_message_content)}. Content: {last_assistant_message_content}")
            # Depending on strictness, could return or raise. For now, attempt to process as empty.
            last_assistant_message_content = []

        for content_block in last_assistant_message_content:
            if content_block.type == "text":
                # Ensure text is printed to the console for the user to see.
                # Logging of this text content might be too verbose for INFO level.
                # Consider DEBUG if needed, or rely on console output.
                print(f"\033[93mClaude\033[0m: {content_block.text}")
            elif content_block.type == "tool_use":
                has_tool_use_in_response = True
                tool_name = content_block.name
                tool_id = content_block.id
                tool_input = content_block.input

                logging.info(f"Tool use requested: {tool_name} with input: {tool_input}")
                print(f"\033[92mtool\033[0m: {tool_name}({json.dumps(tool_input)})")

                if tool_name in self.tools:
                    try:
                        result_content = self.tools[tool_name].execute(tool_input)
                        if not isinstance(result_content, str):
                            result_content = json.dumps(result_content)

                        tool_results_for_next_turn.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_content,
                            "is_error": False,
                        })
                        logging.info(f"Tool {tool_name} executed successfully.")
                    except Exception as e:
                        logging.exception(f"Error executing tool {tool_name}")
                        print(f"Error executing tool {tool_name}: {e}")
                        tool_results_for_next_turn.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": f"Error executing tool {tool_name}: {str(e)}",
                            "is_error": True,
                        })
                else:
                    logging.warning(f"Tool '{tool_name}' not found by agent.")
                    print(f"Tool '{tool_name}' not found by agent.")
                    tool_results_for_next_turn.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": f"Error: Agent does not have a tool named '{tool_name}'.",
                        "is_error": True,
                    })

        return tool_results_for_next_turn, has_tool_use_in_response

    def _append_tool_results_to_conversation(self, tool_results):
        """Appends tool results to the conversation history for the next API call."""
        if not tool_results:
            logging.warning("Attempted to append empty tool results to conversation.")
            return

        # If there were tool uses, the next message to Claude must be the tool results.
        # This message is from the "user" role, containing "tool_result" type content.
        self.conversation.append({
            "role": "user",  # This is correct as per Anthropic's spec for tool results
            "content": tool_results
        })
        logging.info("Appended tool results to conversation.")