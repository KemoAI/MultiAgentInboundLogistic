
"""User Clarification and Routimg to Sub Agents.

This module implements the  the Routing workflow, where we:
1. Assess if the user's data needs clarification
2. Delegate and route to Sub Agents

The workflow uses structured output to make deterministic decisions about
whether sufficient context exists to proceed with Routing.
"""

import json
from dotenv import load_dotenv
from datetime import datetime
from typing_extensions import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage , get_buffer_string
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver

from src.prompt import supervisor_decision_to_route_to_subagents , supervisor_build_subagent_brief , supervisor_update_subagent_brief 
from src.supervisor_schema import AgentState, ClarifyWithUser, AgentInputState, NextAgent

# Load environment variables
load_dotenv()

checkpointer = InMemorySaver()

# ===== IBL FIELDS =====
try:
    with open ("../IBL_SCHEMA.json" , "r") as config_file:
        routing_fields = json.load(config_file)
except FileNotFoundError:
    print("Error: config.json not found. Please create it.")

def get_field_names_description(list_of_field_dicts):
    return [{k: v for k, v in d.items() if k in ['field', 'description']} for d in list_of_field_dicts]

LOGISTICS_FIELDS = get_field_names_description(routing_fields.get("logistics_agent", []))
FORWARDER_FIELDS = get_field_names_description(routing_fields.get("forwarder_agent", []))

AGENT_FIELD_MAP = {
    NextAgent.LOGISTICS_AGENT.value: LOGISTICS_FIELDS,
    NextAgent.FORWARDER_AGENT.value: FORWARDER_FIELDS,
}

# ===== UTILITY FUNCTIONS =====
def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %#d, %Y")

# Set up tools and model binding
tools = []
tools_by_name = {tool.name: tool for tool in tools}

# Initialize model
model = init_chat_model(model="openai:gpt-5.1", temperature=0.0)
model_with_tools = model.bind_tools(tools)

# ===== WORKFLOW NODES =====
def supervisor_agent(state: AgentState):
    """
        Supervisor Agent determines if the input data sufficient to make 
        deterministic decisions and assign the task to the next agent.
    """

    current_agent = None
    for agent_name, status in state.get("agent_status", {}).items():
        if status == "pending_response":
            current_agent = agent_name
            break
    if current_agent:
        updated_briefs = dict(state.get("agent_briefs", {}))                  # Get the agent_briefs
        updated_briefs[current_agent] = model.invoke([                        # Update the pending agent brief based on the last human message
            HumanMessage(content=supervisor_update_subagent_brief.format(
                                                                            agent               = current_agent,
                                                                            relevant_fields     = AGENT_FIELD_MAP[current_agent],
                                                                            current_brief       = updated_briefs.get(current_agent, ""),
                                                                            latest_user_message = state["messages"][-2:],
            ))
        ]).content.strip()

        return {
            "agent_briefs": updated_briefs
        }

    # Set up structured output model
    structured_output_model = model_with_tools.with_structured_output(ClarifyWithUser)

    # Invoke the model with clarification instructions
    response = structured_output_model.invoke([
        HumanMessage(content=supervisor_decision_to_route_to_subagents.format(
                                                                            message             = get_buffer_string(messages=state["messages"]), 
                                                                            date                = get_today_str(),
                                                                            logistics_fields    = get_field_names_description(routing_fields.get("logistics_agent")),
                                                                            forwarder_fields    = get_field_names_description(routing_fields.get("forwarder_agent"))
        ))
    ])

    delegated_agents = [
        agent for agent in list(dict.fromkeys(response.delegate_to))
        if agent in (NextAgent.LOGISTICS_AGENT, NextAgent.FORWARDER_AGENT)
    ]

    agent_briefs = {}
    for agent in delegated_agents:
        agent_name = agent.value
        agent_briefs[agent_name] = model.invoke([
            HumanMessage(content=supervisor_build_subagent_brief.format(
                                                                            agent               = agent_name,
                                                                            relevant_fields     = AGENT_FIELD_MAP[agent_name],
                                                                            user_chat_history   = state["messages"],
                                                                            routing_brief       = response.agent_brief,
            ))
        ]).content.strip()

    return {
             "clarification_schemas" : response ,
             "agent_brief" : response.agent_brief,
             "agent_briefs": agent_briefs,
             "list_of_agents": list(dict.fromkeys(response.delegate_to)),
             "agent_status": {agent.value: "pending_response" for agent in delegated_agents}
           }

def supervisor_tools(state: AgentState):
    """
        Executes all tool calls from the Supervisor Agent response.
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

def clarify_with_user(state: AgentState):
    """In Case the user needs to be asked a clarifying question."""
    clarification_schemas = state.get("clarification_schemas")
    if clarification_schemas and clarification_schemas.question:
        question = clarification_schemas.question
    return {"messages": [AIMessage(content=question)]}

def DelegateNextAgent(state: AgentState) -> Literal["logistics_agent", "forwarder_agent", "supervisor_tools", "clarify_with_user"]:

    """ 
        A routing logic that uses the supervisor agent's responses to determine 
        which agent should be assigned the task next 
    """

    list_of_agents = state.get("list_of_agents", [])

    # Then check the routing decision
    clarification_schemas = state.get("clarification_schemas")
    if not list_of_agents or not clarification_schemas:
        return "__end__"

    next_agent = list_of_agents[0]

    if next_agent == NextAgent.LOGISTICS_AGENT:
        return "logistics_agent"
    elif next_agent == NextAgent.FORWARDER_AGENT:
        return "forwarder_agent"
    elif next_agent == NextAgent.CLARIFY_WITH_USER:
        return "clarify_with_user"
    else:
        return "__end__"

def logistics_agent(state: AgentState):
    pass

def forwarder_agent(state: AgentState):
    pass

# ===== GRAPH CONSTRUCTION =====

# Build the scoping workflow
supervisor_agent_builder = StateGraph(AgentState, input_schema=AgentInputState)

# Add workflow nodes
supervisor_agent_builder.add_node("supervisor_agent"  , supervisor_agent)
supervisor_agent_builder.add_node("supervisor_tools"  , supervisor_tools)
supervisor_agent_builder.add_node("clarify_with_user" , clarify_with_user)
supervisor_agent_builder.add_node("logistics_agent"   , logistics_agent)
supervisor_agent_builder.add_node("forwarder_agent"   , forwarder_agent)

# Add workflow edges
supervisor_agent_builder.add_edge(START, "supervisor_agent")
supervisor_agent_builder.add_conditional_edges(
    "supervisor_agent",
     DelegateNextAgent,
    {
        "supervisor_tools" : "supervisor_tools"  , # execute tools,
        "clarify_with_user": "clarify_with_user" , # Provide final answer
        "logistics_agent"  : "logistics_agent" ,
        "forwarder_agent"  : "forwarder_agent"
    },
)
supervisor_agent_builder.add_edge("supervisor_tools", "supervisor_agent")
supervisor_agent_builder.add_edge("clarify_with_user", END)

# Compile the workflow
SupervisorAgent = supervisor_agent_builder.compile(checkpointer = checkpointer)
