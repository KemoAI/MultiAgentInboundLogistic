
"""State Definitions and Pydantic Schemas for Forwarder Agent.

This defines the state objects and structured schemas used for
the Forwarder Agent scoping workflow, including Forwarder state management and output schemas.
"""

import operator
from datetime import date
from typing_extensions import Optional, Annotated, List, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field , create_model
from src.supervisor_schema import AgentState
from src.ibl_data_source import ibl_data_source

# Load logitics fields dynamiclly
logistics_fields = ibl_data_source("../ibl_schema.json","logistics_agent")

# Dynamically create Pydantic model for shipment fields
DynamicShipmentFields = create_model(
    "DynamicShipmentFields",
    **{
        field_item["field"]: (
            Optional[field_item["dataType"]],  # default type; could later map dataType
            Field(None, description = field_item.get("description", ""))
        )
        for field_item in logistics_fields
    }
)

# ===== STRUCTURED OUTPUT SCHEMAS =====

class ForwarderSchema(BaseModel):
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

# ===== STATE DEFINITIONS =====

class ForwarderState(AgentState):
    """ State for the Logistics Agent """
    agent_response: Optional[LogisticsSchema] = None
