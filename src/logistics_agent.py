
"""This code contains the code for the logistician agent"""

from datetime import datetime
from typing_extensions import Literal

from langchain.chat_models import init_chat_model
from langchain_community.chat_models import ChatDeepInfra
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
import os
from src.prompt import missing_mandatory_fields_prompt, missing_optional_fields_prompt, \
                        logistics_confirmation_prompt, logistics_prompt, summarize_logistics_system_prompt, \
                        summarize_logistics_human_prompt
from src.logistics_schema import LogisticsSchema, LogisticsState

# ===== UTILITY FUNCTIONS =====

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %#d, %Y")

# ===== CONFIGURATION =====

# Initialize model
model = init_chat_model(model="openai:gpt-4.1", temperature=0.0)
summarize_model = model

tools = []
tools_by_name = {tool.name: tool for tool in tools}

# Bind model with tools
model = model.bind_tools(tools)

def logistics_agent(state: LogisticsState) -> Command[Literal["__end__", "logistics_tools", "confirm_with_user", "commit_logistics_transaction"]]:
    """

    """
    # Set up structured output model
    structured_output_model = model.with_structured_output(LogisticianSchema)

    # Invoke the model with clarification instructions
    response = structured_output_model.invoke([
        HumanMessage(content=logistician_prompt.format(
            agent_brief=state["agent_brief"], 
            date=get_today_str()
        ))
    ])

    if response.tool_calls: # if it needs a tool
        return Command(
            goto="logistics_tools", 
            update={"supervisor_messages": [response]}
        )
    elif response.missing_mandatory_fields: # if there is a missing mandatory fields
        return Command(
            goto=END, 
            update={"messages": [AIMessage(content=missing_mandatory_fields_prompt.format(
                missing_fields=response.missing_mandatory_fields))]}
        )
    elif response.missing_optional_fields and not response.is_confirmed_by_user: # missing optional fields before confirmation
        return Command(
            goto=END, 
            update={"messages": [AIMessage(content=missing_optional_fields_prompt.format(
                missing_fields=response.missing_optional_fields))]}
        )
    elif not response.is_confirmed_by_user: # missing confirmation
        return Command(
            goto="confirm_with_user", 
            update={"supervisor_messages": [response]}
        )
    else: # everything is OK and confirmed
        return Command(
            goto="commit_logistics_transaction", 
            update={"supervisor_messages": [response]}
        )

def confirm_with_user(state: LogisticsState) -> Command[Literal["__end__"]]: 
    """In case the logistician needs to confirm something with the user"""
    # first summarize 
    system_message = summarize_logistics_system_prompt.format(date=get_today_str())
    messages = [SystemMessage(content=system_message)] + state.get("supervisor_messages", []) + [HumanMessage(content=summarize_logistics_human_prompt)]
    response = summarize_model.invoke(messages)
    # Print the summary requesting confirmation
    return Command(
        goto=END, 
        update={"messages": [AIMessage(content=logistics_confirmation_prompt.format(summary=response.content))]}
    )

def logistics_tools(state: LogisticsState):
    """Execute all tool calls from the previous LLM response.

    Executes all tool calls from the previous LLM responses.
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

def commit_logistics_transaction(state: LogisticsState):
    """ """
    # get the last response which includes all the filled values after confirmation
    messages = state["supervisor_messages"]
    last_message = messages[-1]
    # fill it 

    # commit it using some API or something

    # return small confirmation message
    return{
        "messages": [AIMessage(content="Small confirmation message")]
    }

# Build the scoping workflow
logistics_agent_builder = StateGraph(LogisticsState)

# Add workflow nodes
logistics_agent_builder.add_node("logistics_agent", logistics_agent)
logistics_agent_builder.add_node("logistics_tools", logistics_tools)
logistics_agent_builder.add_node("confirm_with_user", confirm_with_user)
logistics_agent_builder.add_node("commit_logistics_transaction", commit_logistics_transaction)

# Add workflow edges
logistics_agent_builder.add_edge(START, "logistics_agent")
logistics_agent_builder.add_edge("logistics_tools", "logistics_agent")
logistics_agent_builder.add_edge("commit_logistics_transaction", END)

# Compile the workflow
logistics_agent = logistics_agent_builder.compile()
