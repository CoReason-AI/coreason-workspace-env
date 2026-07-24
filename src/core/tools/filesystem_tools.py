"""
Unified Filesystem Tools — Parity with Gemini, Antigravity, Claude Code, and Windsurf.
Provides view_file, write_file, replace_file_content, multi_replace, grep_search, and list_dir.
"""
import os
import re
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool


@tool
def view_file_tool(path: str, start_line: Optional[int] = 1, end_line: Optional[int] = 800) -> Dict[str, Any]:
    """
    View contents of a file from start_line to end_line (1-indexed).
    Parity with Gemini/Antigravity view_file.
    """
    if not os.path.exists(path):
        return {"error": f"File '{path}' does not exist."}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        s_idx = max(0, (start_line or 1) - 1)
        e_idx = min(total_lines, end_line or total_lines)
        
        selected = lines[s_idx:e_idx]
        formatted = "".join(f"{i + s_idx + 1}: {line}" for i, line in enumerate(selected))
        
        return {
            "path": path,
            "total_lines": total_lines,
            "showing_start": s_idx + 1,
            "showing_end": e_idx,
            "content": formatted,
        }
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}


@tool
def write_file_tool(path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
    """
    Create a new file or overwrite an existing file.
    Parity with write_to_file.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        if os.path.exists(path) and not overwrite:
            return {"error": f"File '{path}' already exists and overwrite is set to False."}
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return {"status": "success", "path": path, "bytes_written": len(content)}
    except Exception as e:
        return {"error": f"Failed to write file: {str(e)}"}


@tool
def replace_file_content_tool(path: str, target_content: str, replacement_content: str) -> Dict[str, Any]:
    """
    Replaces a single contiguous block of text in a file.
    Parity with replace_file_content.
    """
    if not os.path.exists(path):
        return {"error": f"File '{path}' does not exist."}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            full_text = f.read()
        
        if target_content not in full_text:
            return {"error": f"Target content not found in '{path}'."}
        
        updated = full_text.replace(target_content, replacement_content, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated)
            
        return {"status": "success", "path": path}
    except Exception as e:
        return {"error": f"Failed to replace content: {str(e)}"}


@tool
def grep_search_tool(search_path: str, query: str) -> List[Dict[str, Any]]:
    """
    Searches for pattern matches across files in a directory.
    Parity with ripgrep / grep_search.
    """
    results = []
    if not os.path.exists(search_path):
        return [{"error": f"Path '{search_path}' does not exist."}]
    
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    
    for root, _, files in os.walk(search_path):
        if ".git" in root or "__pycache__" in root or ".venv" in root:
            continue
        for file in files:
            full_p = os.path.join(root, file)
            try:
                with open(full_p, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            results.append({
                                "file": full_p.replace("\\", "/"),
                                "line_number": line_num,
                                "line_content": line.strip()
                            })
                            if len(results) >= 50:
                                return results
            except Exception:
                continue
                
    return results


@tool
def list_dir_tool(directory_path: str) -> Dict[str, Any]:
    """
    Lists files and directories under a path.
    Parity with list_dir.
    """
    if not os.path.exists(directory_path):
        return {"error": f"Directory '{directory_path}' does not exist."}
    
    try:
        items = []
        for name in os.listdir(directory_path):
            p = os.path.join(directory_path, name)
            items.append({
                "name": name,
                "is_dir": os.path.isdir(p),
                "size_bytes": os.path.getsize(p) if os.path.isfile(p) else 0
            })
        return {"path": directory_path, "items": items}
    except Exception as e:
        return {"error": f"Failed to list directory: {str(e)}"}
