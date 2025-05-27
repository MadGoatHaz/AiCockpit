from pydantic import BaseModel, Field, ConfigDict # Import ConfigDict
from typing import List, Optional
import datetime 

class FileNode(BaseModel):
    model_config = ConfigDict(extra="forbid") # Updated

    name: str = Field(..., min_length=1, description="Name of the file or directory.")
    path: str = Field(..., description="Relative path from the session's data root, using forward slashes.")
    is_dir: bool = Field(..., description="True if this node is a directory, False if it's a file.")
    size_bytes: Optional[int] = Field(None, ge=0, description="Size of the file in bytes. Must be non-negative if set.")
    modified_at: str = Field(..., description="ISO timestamp of the last modification time.")

class ListDirRequest(BaseModel): 
    model_config = ConfigDict(extra="forbid") # Updated

    path: str = Field(".", description="Relative path of the directory to list. Defaults to the root.")

class ReadFileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid") # Updated

    path: str = Field(..., description="Relative path of the file read.")
    content: str = Field(..., description="Content of the file (assumes text).")
    encoding: str = Field("utf-8", description="Encoding of the file content.")

class WriteFileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid") # Updated

    path: str = Field(..., description="Relative path of the file to write/overwrite.")
    content: str = Field(..., description="Content to write to the file.")
    encoding: str = Field("utf-8", description="Encoding to use when writing the file.")

class CreateDirectoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid") # Updated

    path: str = Field(..., description="Relative path of the directory to create.")

class MoveItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid") # Updated

    source_path: str = Field(..., description="Current relative path of the item to move/rename.")
    destination_path: str = Field(..., description="New relative path for the item.")
