from agent.agent import Agent, ToolDefinition
from tools.file_tools import read_file, list_files, edit_file, new_file
from tools.schemas import ReadFileInput, ListFilesInput, EditFileInput, NewFileInput
import sys

# Define tool definitions
read_file_tool = ToolDefinition(
    name="read_file",
    description="Read the contents of a given relative file path. Use this when you want to see what's inside a file. Do not use this with directory names.",
    input_schema=ReadFileInput,
    func=read_file
)

list_files_tool = ToolDefinition(
    name="list_files",
    description="List files and directories at a given path. If no path is provided, lists files in the current directory.",
    input_schema=ListFilesInput,
    func=list_files
)

edit_file_tool = ToolDefinition(
    name="edit_file",
    description="Make edits to a text file. Replaces 'old_str' with 'new_str' in the given file. 'old_str' and 'new_str' MUST be different from each other. If the file specified with path doesn't exist, it will be created.",
    input_schema=EditFileInput,
    func=edit_file
)

new_file_tool = ToolDefinition(
    name="new_file",
    description="Create a new file at the specified path with the given content. Overwrites if the file already exists.",
    input_schema=NewFileInput,
    func=new_file
)

def get_user_message():
    try:
        return input("\033[94mYou\033[0m: ")
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        return None

def main():
    tools = [read_file_tool, list_files_tool, edit_file_tool, new_file_tool]
    agent = Agent(get_user_message, tools)
    agent.run()

if __name__ == "__main__":
    main()
