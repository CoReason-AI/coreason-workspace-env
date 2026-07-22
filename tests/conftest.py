import sys
import asyncio
import pytest
import os

# Test with tracing disabled to prevent test failures on missing credentials
os.environ["LANGCHAIN_TRACING_V2"] = "false"

if sys.platform == 'win32':
    # Psycopg requires SelectorEventLoop on Windows for async mode
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
