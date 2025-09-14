
"""Supervisor Definitions and Pydantic Schemas for Routing Workflow.

This defines the state objects and structured schemas used for Routing to 
sub agent sworkflow, including Supervisor state management and output schemas.
"""

import operator
from typing_extensions import Optional, Annotated, List, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from enum import Enum

# ===== STRUCTURED OUTPUT SCHEMAS =====

class NextAgent(str, Enum):
    END = "__end__"
    CLARIFY_WITH_USER = "clarify_with_user"
    LOGISTICIAN_AGENT = "logistician_agent"
    CLEARANCE_AGENT   = "clearance_agent"
    SUPERVISOR_TOOLS  = "supervisor_tools"

class ClarifyWithUser(BaseModel):
    """Schema for delegation decision and questions."""
    question: str = Field(
        description = "A question to ask the user to clarify the report scope",
    )
    delegate_to: NextAgent = Field(
        description = "A decision to delegate and route the task to the next agent",
    )
    agent_brief: str = Field(
        description = "A Brief that will be used to route the task to the next sub-agent",
    )

class AgentInputState(MessagesState):
    """Input state for the full agent - only contains messages from user input."""
    pass

class AgentState(MessagesState):
    """
    Main state for the full multi-agent system.

    Extends MessagesState with additional fields for routing coordination.
    """

    supervisor_messages: Annotated[Sequence[BaseMessage], add_messages]
    clarification_schemas: Optional[ClarifyWithUser] = None
    agent_brief: str
