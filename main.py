from agent.agent import Agent, ToolDefinition
from tools.file_tools import read_file, list_files, edit_file, new_file
from tools.schemas import ReadFileInput, ListFilesInput, EditFileInput, NewFileInput
# import sys # Unused import

# Define tool definitions
read_file_tool = ToolDefinition(
    name="read_file",
    description="Read the contents of a given relative file path. Use this when you want to see what's inside a file. Do not use this with directory names.",
    input_schema=ReadFileInput,
    func=read_file
)

list_files_tool = ToolDefinition(
    name="list_files",
    description="List files and directories within a specified directory path (non-recursive). If no path is provided, lists contents of the current directory. Directories in the output list are appended with a '/'. Hidden files/directories are included.",
    input_schema=ListFilesInput,
    func=list_files
)

edit_file_tool = ToolDefinition(
    name="edit_file",
    description="Edits a file by replacing the first occurrence of 'old_str' with 'new_str'. "
                "'old_str' and 'new_str' must be different. "
                "If 'old_str' is an empty string and the file exists, 'new_str' will be prepended to the file's content. "
                "If the file specified by 'path' does not exist AND 'old_str' is an empty string, a new file will be created with 'new_str' as its content. "
                "If 'old_str' is not empty and not found in the file, an error will be raised. "
                "An error is also raised if the path is empty.",
    input_schema=EditFileInput,
    func=edit_file
)

new_file_tool = ToolDefinition(
    name="new_file",
    description="Create a new file at the specified path with the given content. If the file already exists, it will be overwritten. Parent directories will be created if they do not exist.",
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
