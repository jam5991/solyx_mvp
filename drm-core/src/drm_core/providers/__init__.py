from .vastai import VastAIProvider
from .lambdalabs import LambdaLabsProvider
from .coreweave import CoreWeaveProvider
from typing import List, Dict, Any

async def query_lambda_labs() -> List[Dict[str, Any]]:
    """Mock function for querying Lambda Labs API"""
    return []

async def query_vast_ai() -> List[Dict[str, Any]]:
    """Mock function for querying Vast.ai API"""
    return []

__all__ = ['VastAIProvider', 'LambdaLabsProvider', 'CoreWeaveProvider', 'query_lambda_labs', 'query_vast_ai']
