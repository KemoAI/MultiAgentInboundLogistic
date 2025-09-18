
"""This code contains the code for the logistician agent"""
import os
import json
from datetime import datetime
from typing_extensions import Literal

from langchain.chat_models import init_chat_model
from langchain_community.chat_models import ChatDeepInfra
from langchain_core.messages import SystemMessage , HumanMessage, AIMessage, get_buffer_string
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver
from src.prompt import missing_mandatory_fields_prompt, missing_optional_fields_prompt, \
                        logistics_confirmation_prompt, logistics_agent_tasks
from src.logistics_schema import LogisticsSchema, LogisticsState

# ===== UTILITY FUNCTIONS =====

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %#d, %Y")

# ===== IBL FIELDS =====
try:
    with open ("../logistics_schema.json" , "r") as config_file:
        logistics_schema_fields = json.load(config_file).get('logistics_schema', [])
except FileNotFoundError:
    print("Error: logistics_schema.json not found. Please create it.")
    exit()

# Process the fields
mandatory_fields = [
    item['field'] for item in logistics_schema_fields if item.get('required') is True
]
optional_fields = [
    item['field'] for item in logistics_schema_fields if item.get('required') is False
]

def get_selected_field_details(all_fields, selected_fields):
    """
    """
    return [ detail for detail in all_details if detail['field'] in selected_fields]

# ===== CONFIGURATION =====

# Initialize model
model = init_chat_model(model="openai:gpt-4.1", temperature=0.0)
summarize_model = model

tools = []
tools_by_name = {tool.name: tool for tool in tools}

# Bind model with tools
model = model.bind_tools(tools)

def logistics_agent(state: LogisticsState) -> Command[Literal["logistics_tools", "ConfirmWithUser", "CommitLogisticsTransaction" , "__end__"]]:
    """
       Logistics Agent assesses whether the received data is adequate to make deterministic decisions 
       about committing the data to the logistics database.
    """
    # Set up structured output model
    structured_output_model = model.with_structured_output(LogisticsSchema)

    # Invoke the model
    response = structured_output_model.invoke([
               HumanMessage(content=logistics_agent_tasks.format(
                                    agent_brief = get_buffer_string(state["agent_brief"]), 
                                    date = get_today_str(),
                                    fields_details=logistics_schema_fields,
                                    mandatory_fields=mandatory_fields,
                                    optional_fields=optional_fields
               ))
    ])

    if response.missing_mandatory_fields:        # missing mandatory fields
        return Command(
               goto=END, 
               update={"messages": [AIMessage(content=missing_mandatory_fields_prompt.format(
                                                     missing_fields = response.missing_mandatory_fields,
                                                     missing_field_details = get_selected_field_details(all_fields = logistics_schema_fields,
                                                                                                        selected_fields = response.missing_mandatory_fields))
                                                     )]}
        )
    elif response.missing_optional_fields and response.ask_for_optional_fields: # missing optional fields before confirmation
        return Command(
               goto=END, 
               update={"messages": [AIMessage(content=missing_optional_fields_prompt.format(
                                              missing_fields = response.missing_optional_fields,
                                              missing_field_details = get_selected_field_details(all_fields = logistics_schema_fields,
                                                                                                 selected_fields = response.missing_optional_fields))
                                                     )]}
        )
    elif response.needs_user_confirmation: # missing confirmation
        return Command(
               goto="ConfirmWithUser", 
               update={"agent_response": response}
        )
    else: # everything is OK and confirmed
        return Command(
               goto="CommitLogisticsTransaction", 
               update={"agent_response": response}
        )

def ConfirmWithUser(state: LogisticsState) -> Command[Literal["__end__"]]: 
    """ If there is anything that Logistics Agent needs to confirm with the user """
    # first summarize 
    # system_message = summarize_logistics_system_prompt.format(date=get_today_str())
    # messages = [SystemMessage(content=system_message)] + state.get("messages", []) + [HumanMessage(content=summarize_logistics_human_prompt)]
    # response = summarize_model.invoke(messages)
    # Print the summary requesting confirmation
    return Command(
           goto=END, 
           update={"messages": [AIMessage(content=logistics_confirmation_prompt.format(information_report=state["agent_response"].model_dump()))]}
    )

def logistics_tools(state: LogisticsState):
    """
        Executes all tool calls from the logistics Agent response.
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

def CommitLogisticsTransaction(state: LogisticsState):
    """ Following the user's confirmation, the logistics database will be updated with the received data """
    # get the last response which includes all the filled values after confirmation
    response = state["agent_response"]

    # Convert the response into dictionary and delete unnecessary fields
    response_dict = response.model_dump()
    response_dict = {k:v for (k,v) in response_dict.items() if k not in ["missing_mandatory_fields", "missing_optional_fields",
                                                                         "ask_for_optional_fields", "needs_user_confirmation"]}
    # commit the logistics transactions following the confirmation
    confirmation_result = UpdateDB.invoke({"record": response_dict})

    return{
            "messages": [AIMessage(content=f"{confirmation_result}")]     # confirm back
    }

# Build the scoping workflow
logistics_agent_builder = StateGraph(LogisticsState)

# Add workflow nodes
logistics_agent_builder.add_node("logistics_agent", logistics_agent)
logistics_agent_builder.add_node("logistics_tools", logistics_tools)
logistics_agent_builder.add_node("ConfirmWithUser", ConfirmWithUser)
logistics_agent_builder.add_node("CommitLogisticsTransaction", CommitLogisticsTransaction)

# Add workflow edges
logistics_agent_builder.add_edge(START, "logistics_agent")
logistics_agent_builder.add_edge("logistics_tools", "logistics_agent")
logistics_agent_builder.add_edge("ConfirmWithUser", END)
logistics_agent_builder.add_edge("CommitLogisticsTransaction", END)

# Compile the workflow
checkpointer = InMemorySaver()
LogisticsAgent = logistics_agent_builder.compile(checkpointer = checkpointer)
