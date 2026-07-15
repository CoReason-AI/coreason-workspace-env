import os
from langchain_core.tools import tool

@tool
def local_fs_writer(filepath: str, content: str) -> str:
    """Writes the content string to the exact filepath on the local filesystem."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"

@tool
def local_fs_reader(filepath: str) -> str:
    """Reads the content of a file from the local filesystem."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
