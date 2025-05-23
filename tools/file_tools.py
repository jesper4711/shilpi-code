import os
import json
from typing import List
from .schemas import ReadFileInput, ListFilesInput, EditFileInput, NewFileInput

def read_file(input_data: dict) -> str:
    data = ReadFileInput(**input_data)
    with open(data.path, 'r', encoding='utf-8') as f:
        return f.read()

def list_files(input_data: dict) -> str:
    data = ListFilesInput(**input_data)
    dir_path = data.path or '.'
    files = []
    for root, dirs, filenames in os.walk(dir_path):
        for d in dirs:
            files.append(os.path.relpath(os.path.join(root, d), dir_path) + '/')
        for fn in filenames:
            files.append(os.path.relpath(os.path.join(root, fn), dir_path))
        break  # Do not descend into subdirectories
    return json.dumps(files)

def edit_file(input_data: dict) -> str:
    data = EditFileInput(**input_data)
    if data.path == '' or data.old_str == data.new_str:
        raise ValueError('invalid input parameters')
    try:
        with open(data.path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        if data.old_str == '':
            return new_file({'path': data.path, 'content': data.new_str})
        else:
            raise
    if data.old_str not in content:
        raise ValueError('old_str not found in file')
    new_content = content.replace(data.old_str, data.new_str, 1)
    with open(data.path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return f"Edited {data.path} successfully."

def new_file(input_data: dict) -> str:
    data = NewFileInput(**input_data)
    os.makedirs(os.path.dirname(data.path), exist_ok=True) if os.path.dirname(data.path) else None
    with open(data.path, 'w', encoding='utf-8') as f:
        f.write(data.content)
    return f"Successfully created file {data.path}"
