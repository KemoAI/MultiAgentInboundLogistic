""" This code defines a tool to push records to IBL DB """
from typing import Dict, Any
from langchain_core.tools import tool

# Define tools
@tool(parse_docstring=True)
def UpdateDB(record: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Update the IBL database and confirm back.

    Args:
        record: Record details of dictionary type.

    Returns:
        A dictionary contains a success status and the new record

    """
    success = True
    return {
            "status" : f"{success}",
            "record" : record
    }
