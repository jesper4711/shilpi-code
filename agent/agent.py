# agent.py
import json
import os
from typing import Callable, List # Removed Dict, Any as they weren't strictly necessary for this part
from anthropic import Anthropic # Removed AsyncAnthropic, HUMAN_PROMPT, AI_PROMPT as not used
from dotenv import load_dotenv

load_dotenv()

class ToolDefinition:
    def __init__(self, name: str, description: str, input_schema, func: Callable[[dict], str]):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.func = func

    def execute(self, input_data: dict) -> str:
        # Validate input_data against schema if needed, though Pydantic in tools does this.
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
                if user_input is None: # Handle Ctrl-C or EOF
                    break
                self.conversation.append({"role": "user", "content": user_input})

            # Send conversation to Anthropic
            try:
                # print(f"DEBUG: Sending to Claude: {json.dumps(self.conversation, indent=2)}") # For debugging
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2048, # Increased max_tokens slightly just in case
                    messages=self.conversation,
                    tools=self.anthropic_tools(),
                )
            except Exception as e:
                print(f"Anthropic API error: {e}")
                # Decide if you want to break or allow retry, for now, break.
                break

            # --- Response Processing ---
            # The assistant's response (raw API response.content) must be added to the conversation.
            # response.content is a list of content blocks (e.g., text, tool_use).
            if response.content:
                self.conversation.append({
                    "role": "assistant",
                    "content": response.content # This is already a list of content blocks
                })
            else:
                # This case should ideally not happen with a successful API call
                # If it does, append an empty content list for the assistant.
                self.conversation.append({
                    "role": "assistant",
                    "content": []
                })


            # Now, iterate through the content blocks of the *just added* assistant message
            # to execute tools and prepare tool_results for the *next* user message.
            tool_results_for_next_turn = []
            has_tool_use_in_response = False

            # Ensure we are looking at the last assistant message's content
            last_assistant_message_content = self.conversation[-1]["content"] if self.conversation and self.conversation[-1]["role"] == "assistant" else []


            for content_block in last_assistant_message_content:
                if content_block.type == "text":
                    print(f"\033[93mClaude\033[0m: {content_block.text}")
                elif content_block.type == "tool_use":
                    has_tool_use_in_response = True
                    tool_name = content_block.name
                    tool_id = content_block.id
                    tool_input = content_block.input

                    # Print the tool being called for visibility
                    print(f"\033[92mtool\033[0m: {tool_name}({json.dumps(tool_input)})")

                    if tool_name in self.tools:
                        try:
                            result_content = self.tools[tool_name].execute(tool_input)
                            # Anthropic expects tool result 'content' to be a string or list of content blocks.
                            # If your tool returns a simple string (like JSON string), that's fine.
                            # If it returns structured data (e.g. a Python list/dict that's not a JSON string),
                            # you should serialize it to a string (e.g., using json.dumps).
                            if not isinstance(result_content, str):
                                result_content = json.dumps(result_content)

                            tool_results_for_next_turn.append({
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": result_content,
                                "is_error": False,
                            })
                        except Exception as e:
                            print(f"Error executing tool {tool_name}: {e}")
                            tool_results_for_next_turn.append({
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": f"Error executing tool {tool_name}: {str(e)}", # Content must be a string or list of blocks
                                "is_error": True,
                            })
                    else:
                        print(f"Tool '{tool_name}' not found by agent.")
                        tool_results_for_next_turn.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": f"Error: Agent does not have a tool named '{tool_name}'.",
                            "is_error": True,
                        })

            if has_tool_use_in_response:
                # If there were tool uses, the next message to Claude must be the tool results.
                # This message is from the "user" role, containing "tool_result" type content.
                self.conversation.append({
                    "role": "user",
                    "content": tool_results_for_next_turn
                })
                read_user_input = False # Claude will process the tool results and respond.
            else:
                # If Claude just talked (no tool use), it's the user's turn to talk next.
                read_user_input = True