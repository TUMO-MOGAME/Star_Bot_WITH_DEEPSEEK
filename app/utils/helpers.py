import os
import uuid
from typing import List

def generate_unique_id() -> str:
    """Generate a unique ID for files and documents."""
    return str(uuid.uuid4())

def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename."""
    return os.path.splitext(filename)[1].lower()

def is_allowed_file(filename: str, allowed_extensions: List[str]) -> bool:
    """Check if a file has an allowed extension."""
    return get_file_extension(filename) in allowed_extensions
