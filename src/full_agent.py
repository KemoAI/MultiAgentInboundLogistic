
"""This code contains the code for the logistician agent"""

import os
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from src.supervisor_schema import AgentInputState
from src.supervisor_agent import DelegateNextAgent, clarify_with_user, supervisor_agent, supervisor_tools
from src.logistics_agent import LogisticsAgent , LogisticsState

# Build the scoping workflow
full_agent_builder = StateGraph(LogisticsState, input_schema=AgentInputState)

# Add workflow nodes
full_agent_builder.add_node("supervisor_agent", supervisor_agent)
full_agent_builder.add_node("supervisor_tools", supervisor_tools)
full_agent_builder.add_node("clarify_with_user", clarify_with_user)
full_agent_builder.add_node("LogisticsAgent", LogisticsAgent)

# Add workflow edges
full_agent_builder.add_edge(START, "supervisor_agent")
full_agent_builder.add_conditional_edges(
    "supervisor_agent",
     DelegateNextAgent,
    {
        "supervisor_tools"  : "supervisor_tools", 
        "clarify_with_user" : "clarify_with_user", 
        "logistics_agent"   : "LogisticsAgent"
    },
)
full_agent_builder.add_edge("supervisor_tools", "supervisor_agent")
full_agent_builder.add_edge("clarify_with_user", END)

# Compile the workflow
checkpointer = InMemorySaver()
full_agent = full_agent_builder.compile(checkpointer = checkpointer)
