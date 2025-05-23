from pydantic import BaseModel
from typing import Optional

class ReadFileInput(BaseModel):
    path: str

class ListFilesInput(BaseModel):
    path: Optional[str] = None

class EditFileInput(BaseModel):
    path: str
    old_str: str
    new_str: str

class NewFileInput(BaseModel):
    path: str
    content: str
