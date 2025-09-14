
"""State Definitions and Pydantic Schemas for Research Scoping.

This defines the state objects and structured schemas used for
the research agent scoping workflow, including researcher state management and output schemas.
"""

import operator
from typing_extensions import Optional, Annotated, List, Sequence
from datetime import date

from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from enum import Enum

# ===== STATE DEFINITIONS =====

class LogisticianState(MessagesState):
    """State for the logistician agent"""
    supervisor_messages: Annotated[Sequence[BaseMessage], add_messages]
    agent_brief: str

# ===== STRUCTURED OUTPUT SCHEMAS =====

class LogisticianSchema(BaseModel):
    """Schema for logistician router decision making."""
    missing_mandatory_fields: List[str] = Field(
        description="List of missing mandatory fields"
    )
    missing_optional_fields: List[str] = Field(
        description="List of missing optional fields"
    )
    is_confirmed_by_user: bool = Field(
        description="indicates whether has been confirmed by the user or not",
        default=False
    )
    AWB: str = Field(
        description="AWB Description"
    )
    product_temperature: str = Field(
        description="Product Temperature Description",
    )
    handover_to_clearance: Optional[date] = Field(
        description="date of handover to clearance",
    )
    shipment_mode: str = Field(
        description="shipment mode",
    )
