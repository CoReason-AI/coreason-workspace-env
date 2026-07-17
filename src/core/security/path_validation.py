import os
from pathlib import Path
import re

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def validate_safe_path(path_str: str, base_dir: Path = WORKSPACE_ROOT, allow_absolute: bool = False) -> Path:
    """
    Validates that a path is safe and does not escape the base directory (preventing directory traversal).
    """
    # Strict string-based sanitization and validation to remove taint for CodeQL
    if not path_str or not isinstance(path_str, str):
        raise ValueError("Security check failed: path must be a non-empty string.")
    
    path_str = path_str.replace('\\', '/')
    
    # Only allow alphanumeric, underscores, dashes, dots, colons, slashes, tildes, and spaces
    if not re.match(r"^[a-zA-Z0-9_\-\./:~\ ]+$", path_str):
        raise ValueError(f"Security check failed: path contains disallowed characters. Path: {path_str}")
        
    if ".." in path_str:
        raise ValueError("Security check failed: path traversal ('..') is not allowed.")
        
    is_absolute = path_str.startswith("/") or (len(path_str) > 1 and path_str[1] == ':')
    if not allow_absolute and is_absolute:
        raise ValueError("Security check failed: absolute paths are not allowed.")

    resolved_base = os.path.abspath(str(base_dir))
    # Normalize the path to resolve potential traversal segments
    requested_path = os.path.normpath(os.path.join(resolved_base, path_str))
    
    # Strict prefix check (recognized by CodeQL path-injection sanitizer models)
    if not allow_absolute and not requested_path.startswith(resolved_base):
        raise ValueError(f"Security check failed: path '{path_str}' escapes the allowed base directory.")
         
    return Path(requested_path)

def validate_alphanumeric(name: str) -> str:
    """
    Validates that a string is strictly alphanumeric with dashes and underscores.
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValueError(f"Security check failed: '{name}' contains disallowed characters. Only alphanumeric, underscores, and dashes are allowed.")
    return name

def sanitize_log_input(value: str) -> str:
    """
    Sanitizes log input by stripping carriage return and newline characters to prevent log injection.
    """
    return str(value).replace('\r', '').replace('\n', '')

