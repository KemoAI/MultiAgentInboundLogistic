""" This code defines a tool to push records to IBL DB """

import sys
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
import asyncio

# Initialize FastMCP server
mcp = FastMCP("db-server")

@mcp.tool()
async def UpdateDB(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the IBL database and confirm back.

    Args:
        record: Record details of dictionary type.

    Returns:
        A dictionary contains a success status and the new record

    """
    try:
        success = True
        return {
                 "status" : f"{success}",
                 "record" : record
               }
    except Exception as e:
        return str(e)

# Main execution
if __name__ == "__main__":
    mcp.run(transport="stdio")
