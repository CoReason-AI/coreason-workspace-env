import sys
import asyncio
import pytest

if sys.platform == 'win32':
    # Psycopg requires SelectorEventLoop on Windows for async mode
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
