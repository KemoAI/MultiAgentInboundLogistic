
"""Supervisor Definitions and Pydantic Schemas for Routing Workflow.

This defines the state objects and structured schemas used for Routing to 
sub agent sworkflow, including Supervisor state management and output schemas.
"""

import operator
from typing_extensions import Optional, Annotated, List, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.tools import tool, InjectedToolArg

from pydantic import BaseModel, Field
from enum import Enum

# ===== STRUCTURED OUTPUT SCHEMAS =====

class NextAgent(str, Enum):
    END = "__end__"
    CLARIFY_WITH_USER = "clarify_with_user"
    LOGISTICS_AGENT   = "logistics_agent"
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

@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:

    """Tool for strategic reflection on supervisor-related tasks progress and decision-making.

    Use this tool after each task to analyze results and plan next steps systematically.
    This creates a deliberate pause in the task delegation workflow for quality decision-making.

    When to use:
    - After receiving task results: What key information did I find?
    - Before deciding next steps: Do I have enough to proceed confidently?
    - When assessing task delegation to the next agent: What specific information am I still missing?
    - Before concluding the task: Can I provide a complete brief?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good brief?
    4. Strategic decision - Should I continue assessing or provide my answer?

    Args:
        reflection: Your detailed reflection on supervisor-related tasks progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """

    return f"Reflection recorded: {reflection}"
