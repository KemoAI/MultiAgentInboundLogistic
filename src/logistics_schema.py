
"""State Definitions and Pydantic Schemas for Logistics Agent.

This defines the state objects and structured schemas used for
the Logistics Agent scoping workflow, including Logistics state management and output schemas.
"""

import operator
from typing_extensions import Optional, Annotated, List, Sequence
from datetime import date

from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from src.supervisor_schema import AgentState
from enum import Enum

# ===== STRUCTURED OUTPUT SCHEMAS =====

class LogisticsSchema(BaseModel):
    """Schema for Logisticis Agent."""
    missing_mandatory_fields: List[str] = Field(
        description = "Fields required by the schema that are missing from the provided data"
    )
    missing_optional_fields: List[str] = Field(
        description = "Optional fields that are missing from the provided data"
    )
    ask_for_optional_fields: bool = Field(
        description = "Specifies whether the user should be prompted for optional fields",
        default = True
    )
    needs_user_confirmation: bool = Field(
        description = "Specifies whether user confirmation is required for the current record",
        default = True
    )
    AWB_BL: Optional[str] = Field(
        description = "The unique Air Waybill or Bill of Lading number for the shipment"
    )
    Product_Temperature: Optional[str] = Field(
        description = "Temperature requirements or description for the product",
    )
    Shipment_Mode: Optional[str] = Field(
        description = "Mode of shipment (e.g., air, sea, road)",
    )

# ===== STATE DEFINITIONS =====

class LogisticsState(AgentState):
    """ State for the Logistics Agent """
    agent_response: Optional[LogisticsSchema] = None
