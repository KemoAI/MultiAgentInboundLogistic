
"""User Clarification and Routimg to Sub Agents.

This module implements the scoping phase of the Routing workflow, where we:
1. Assess if the user's data needs clarification
2. Delegate and route to Sub Agents

The workflow uses structured output to make deterministic decisions about
whether sufficient context exists to proceed with Routing.
"""

from datetime import datetime
from typing_extensions import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage , get_buffer_string
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver

from src.prompt import decision_to_route_inbound_logistics_tasks
from src.data_structure import AgentState, ClarifyWithUser, AgentInputState, NextAgent

checkpointer = InMemorySaver()
# ===== UTILITY FUNCTIONS =====

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %#d, %Y")

# ===== CONFIGURATION =====

# Initialize model
model = init_chat_model(model="openai:gpt-4.1", temperature=0.0)
tools = []
tools_by_name = {tool.name: tool for tool in tools}

# ===== WORKFLOW NODES =====

def supervisor_agent(state: AgentState):
    """
    Determine if the user's request contains sufficient information to proceed.

    Uses structured output to make deterministic decisions and avoid hallucination.
    Routes to either next agent or ends with a clarification question.
    """
    # Set up structured output model
    structured_output_model = model.with_structured_output(ClarifyWithUser)

    # Invoke the model with clarification instructions
    response = structured_output_model.invoke([
        HumanMessage(content=decision_to_route_inbound_logistics_tasks.format(
            message=get_buffer_string(messages=state["messages"]), 
            date=get_today_str()
        ))
    ])

    # Route based on clarification need
    return {
        "full_schema": response,
        "agent_brief": response.agent_brief,
        "supervisor_messages": [
            AIMessage(content=response.delegate_to.value)
        ]
    }

def clarify_with_user(state: AgentState):
    """In Case the user needs to be asked a clarifying question."""
    full_schema = state.get("full_schema")
    if full_schema and full_schema.question:
        question = full_schema.question
    return {"messages": [AIMessage(content=question)]}

def supervisor_tools(state: AgentState):
    """Executes all tool calls from the previous LLM responses.
       Returns updated state with tool execution results.
    """
    tool_calls = state["supervisor_messages"][-1].tool_calls

    # Execute all tool calls
    observations = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observations.append(tool.invoke(tool_call["args"]))

    # Create tool message outputs
    tool_outputs = [
        ToolMessage(
            content=observation,
            name=tool_call["name"],
            tool_call_id=tool_call["id"]
        ) for observation, tool_call in zip(observations, tool_calls)
    ]

    return {"supervisor_messages": tool_outputs}

def delegate_next_agent(state: AgentState) -> Literal["logistician_agent", "clearance_agent", "supervisor_tools", "clarify_with_user"]:
    """Determine where the control should move next.

    Determines whether the agent should execute the tools,  or provide
    a final answer based on whether the LLM made tool calls.

    Returns:
        "tool_node"  : Continue to tool execution
        "next agent" : Stop and compress research"""

    # Then check the routing decision
    full_schema = state.get("full_schema")
    if not full_schema:
        return "__end__"

    if full_schema.delegate_to == NextAgent.LOGISTICIAN_AGENT:
        return "logistician_agent"
    elif full_schema.delegate_to == NextAgent.CLEARANCE_AGENT:
        return "clearance_agent"
    elif full_schema.delegate_to == NextAgent.CLARIFY_WITH_USER:
        return "clarify_with_user"
    else:
        return "__end__"

def logistician_agent(state: AgentState):
    pass

def clearance_agent(state: AgentState):
    pass

# ===== GRAPH CONSTRUCTION =====

# Build the scoping workflow
supervisor_agent_builder = StateGraph(AgentState, input_schema=AgentInputState)

# Add workflow nodes
supervisor_agent_builder.add_node("supervisor_agent", supervisor_agent)
supervisor_agent_builder.add_node("supervisor_tools", supervisor_tools)
supervisor_agent_builder.add_node("clarify_with_user", clarify_with_user)
supervisor_agent_builder.add_node("logistician_agent", logistician_agent)
supervisor_agent_builder.add_node("clearance_agent", clearance_agent)

# Add workflow edges
supervisor_agent_builder.add_edge(START, "supervisor_agent")
supervisor_agent_builder.add_conditional_edges(
    "supervisor_agent",
    delegate_next_agent,
    {
        "supervisor_tools": "supervisor_tools", # execute tools,
        "clarify_with_user": "clarify_with_user", # Provide final answer
        "logistician_agent": "logistician_agent",
         "clearance_agent": "clearance_agent"
    },
)
supervisor_agent_builder.add_edge("supervisor_tools", "supervisor_agent")
supervisor_agent_builder.add_edge("clarify_with_user", END)

# Compile the workflow
SupervisorAgent = supervisor_agent_builder.compile()
