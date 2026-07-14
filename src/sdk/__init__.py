"""
CoReason Python SDK — programmatic access to the platform.

Usage:
    from src.sdk import CoReasonClient

    client = CoReasonClient()
    agents = client.agents.list()
    health = await client.health()
"""
from src.sdk.client import CoReasonClient

__all__ = ["CoReasonClient"]
