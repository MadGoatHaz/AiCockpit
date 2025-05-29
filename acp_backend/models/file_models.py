"""
ACP Backend - Pydantic Models for File System Operations
"""
from datetime import datetime # Keep for FileNode if truly needed, or remove if not
from typing import Optional, List
from pydantic import BaseModel, Field

class FileMetadata(BaseModel):
    """
    Basic metadata for a file.
    Could be expanded with more details like size, full path, etc.
    """
    filename: str = Field(..., description="Name of the file")
    # Ensure path is relative to the session's data directory to avoid ambiguity
    path: str = Field(..., description="Relative path of the file within the session data directory")
    # last_modified: Optional[datetime] = Field(None, description="Last modified timestamp") # Consider adding later

class FileNode(BaseModel):
    """
    Represents a file or directory in a tree structure.
    """
    id: str # Usually the full relative path
    name: str
    type: str # 'file' or 'folder'
    path: str # Relative path from session data root
    children: Optional[List['FileNode']] = None # For folders
    # last_modified: Optional[datetime] = None # When was it last changed
    # size_bytes: Optional[int] = None # For files

class DirectoryListing(BaseModel):
    """
    Represents the contents of a directory.
    """
    path: str # The path that was listed
    contents: List[FileNode]

class FileContentUpdateRequest(BaseModel):
    content: str = Field(description="The new content of the file.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "print('Hello, world!')"
                }
            ]
        }
    }

# Example usage (for illustration, not part of the model definition itself)
# update_request = FileContentUpdateRequest(content="New file text.")
# print(update_request.model_dump_json(indent=2))

class CreateFileEntityRequest(BaseModel):
    path: str = Field(description="The relative path (including the new name) where the file or folder should be created.")
    type: str = Field(description="Type of entity to create, either 'file' or 'folder'.")
    # content: Optional[str] = Field(None, description="Optional initial content for files.") # Consider for future use

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "path": "new_folder/new_file.txt",
                    "type": "file"
                },
                {
                    "path": "another_new_directory",
                    "type": "folder"
                }
            ]
        }
    } 