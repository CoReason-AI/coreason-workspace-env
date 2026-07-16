"""
AST Validation Tools using libcst.

This module exposes purely deterministic AST validation capabilities
using LangChain v1 `@tool` decorators, enforcing the strict Maker-Checker
mandate for read-only structural validation.
"""

import os
from typing import Dict, Any

import libcst as cst
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class SyntaxValidationRequest(BaseModel):
    file_path: str = Field(..., description="Absolute path to the Python file")


@tool(args_schema=SyntaxValidationRequest)
def ast_validate_syntax(file_path: str) -> str:
    """
    Deterministically validates that a Python file parses into a valid
    Abstract Syntax Tree. Used by Checker nodes before merging code.
    """
    if not os.path.exists(file_path):
        return f"Error: File {file_path} does not exist."
        
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()
        
    try:
        cst.parse_module(source_code)
        return f"Syntax validation passed for {file_path}. CST parsed successfully."
    except cst.ParserSyntaxError as e:
        return f"Syntax Error in {file_path}: {e}"
