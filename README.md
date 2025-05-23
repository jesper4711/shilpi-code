# Claude Tool-Use Python Agent

This project is a Python-based command-line agent that connects to Anthropic's Claude models and supports tool use (function calling) via the Anthropic API. It allows you to chat with Claude and have it call custom tools (functions) you define, such as reading, listing, editing, or creating files.

## Features
- Chat with Claude via the terminal
- Claude can call Python functions ("tools") to interact with your local files
- Supports reading, listing, editing, and creating files
- Follows Anthropic's tool use protocol for function calling

## Requirements
- Python 3.8+
- An Anthropic API key ([get one here](https://console.anthropic.com/))

## Installation
1. Clone this repository:
   ```sh
   git clone <repo-url>
   cd <repo-directory>
   ```
2. (Recommended) Create and activate a virtual environment:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Setup
1. Set your Anthropic API key as an environment variable:
   ```sh
   export ANTHROPIC_API_KEY=sk-ant-...
   ```
   Or create a `.env` file in the project root with:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

## Usage
Run the main script:
```sh
python main.py
```
You will see a prompt:
```
Chat with Claude (Ctrl-C to quit)
You: 
```
Type your question or command. If Claude decides to use a tool, it will print the tool call, execute it, and return the result to Claude for further reasoning.

### Example
```
You: list files in the current directory
Claude: Here is how we can list the files in the current directory:
tool: list_files({})
Claude: [file1.txt, file2.py, ...]
```

## Tool Use Protocol
- When Claude wants to use a tool, it outputs a `tool_use` block.
- The agent executes the tool and sends a `tool_result` block in a new user message.
- Claude then uses the result to continue the conversation.
- This protocol is strictly followed to avoid API errors.

## Adding New Tools
- Define your tool function in `tools/file_tools.py`.
- Add a Pydantic schema for its input in `tools/schemas.py`.
- Register the tool in `main.py` using `ToolDefinition`.

## Troubleshooting
- Ensure your API key is set and valid.
- If you see errors about `tool_use_id`, make sure the tool result is sent immediately after a tool use, and the content is a string.
- For more, see [Anthropic's tool use docs](https://docs.anthropic.com/en/docs/build-with-claude/tool-use).

## License
MIT 