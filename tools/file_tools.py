import os
import json
from typing import List
from .schemas import ReadFileInput, ListFilesInput, EditFileInput, NewFileInput

def read_file(input_data: dict) -> str:
    """
    Reads the content of a specified file.

    Args:
        input_data (dict): A dictionary containing:
            path (str): The path to the file to be read.

    Returns:
        str: The content of the file.

    Raises:
        FileNotFoundError: If the file specified by path does not exist.
        Exception: For other potential I/O errors.
    """
    data = ReadFileInput(**input_data)
    with open(data.path, 'r', encoding='utf-8') as f:
        return f.read()

def list_files(input_data: dict) -> str:
    """
    Lists files and directories in a specified path.
    This is non-recursive (only lists top-level contents).
    Includes hidden files and directories.

    Args:
        input_data (dict): A dictionary containing:
            path (str, optional): The directory path to list. Defaults to current directory '.'.

    Returns:
        str: A JSON string representing a list of file and directory names.
             Directories are appended with a '/'.
    """
    data = ListFilesInput(**input_data)
    dir_path = data.path or '.'  # Default to current directory if path is empty or None
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(f"The specified path '{dir_path}' is not a directory or does not exist.")

    items_in_directory = []
    for name in os.listdir(dir_path): # Changed 'entry' to 'name' for consistency with list variable
        if os.path.isdir(os.path.join(dir_path, name)):
            items_in_directory.append(name + "/")
        else:
            items_in_directory.append(name)
    return json.dumps(items_in_directory)


def edit_file(input_data: dict) -> str:
    """
    Edits a file by replacing the first occurrence of an old string with a new string.

    Special behaviors:
    - If `path` is empty or `old_str` is the same as `new_str`, it raises a ValueError.
    - If the file specified by `path` does not exist AND `old_str` is empty,
      it creates a new file with `new_str` as its content.
    - If the file exists AND `old_str` is empty, `new_str` is inserted at the
      beginning of the file content.
    - If `old_str` is not found in the file, it raises a ValueError.

    Args:
        input_data (dict): A dictionary containing:
            path (str): The path to the file to be edited.
            old_str (str): The string to be replaced.
            new_str (str): The string to replace `old_str` with.

    Returns:
        str: A success message indicating the file was edited or created.

    Raises:
        ValueError: If input parameters are invalid, or `old_str` is not found.
        FileNotFoundError: If the file does not exist and `old_str` is not empty.
        Exception: For other potential I/O errors.
    """
    data = EditFileInput(**input_data)
    if not data.path: # Check for empty path specifically
        raise ValueError("File path cannot be empty.")
    if data.old_str == data.new_str:
        raise ValueError("old_str and new_str cannot be the same. No change would be made.")

    try:
        with open(data.path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        if data.old_str == '':
            # Create a new file if old_str is empty and file doesn't exist
            # This behavior should be clearly documented in the tool description for the LLM
            return new_file({'path': data.path, 'content': data.new_str})
        else:
            # Raise FileNotFoundError if old_str is not empty and file doesn't exist
            raise FileNotFoundError(f"The file '{data.path}' was not found.")

    if data.old_str == '':
        # If old_str is empty and file exists, prepend new_str to the content
        new_content = data.new_str + content
    elif data.old_str not in content:
        raise ValueError(f"The string '{data.old_str}' was not found in the file '{data.path}'.")
    else:
        new_content = content.replace(data.old_str, data.new_str, 1)

    with open(data.path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return f"Edited '{data.path}' successfully."

def new_file(input_data: dict) -> str:
    """
    Creates a new file with the specified content or overwrites an existing file.
    If parent directories in the path do not exist, they will be created.

    Args:
        input_data (dict): A dictionary containing:
            path (str): The path where the file should be created/overwritten.
            content (str): The content to write to the file.

    Returns:
        str: A success message indicating the file was created/overwritten.

    Raises:
        ValueError: If the path is empty.
        Exception: For other potential I/O errors.
    """
    data = NewFileInput(**input_data)
    if not data.path:
        raise ValueError("File path cannot be empty for new_file.")

    # Ensure parent directories exist
    dir_name = os.path.dirname(data.path)
    if dir_name: # Only call makedirs if there's a directory part
        os.makedirs(dir_name, exist_ok=True)

    with open(data.path, 'w', encoding='utf-8') as f:
        f.write(data.content)
    return f"Successfully created/overwritten file '{data.path}'."
