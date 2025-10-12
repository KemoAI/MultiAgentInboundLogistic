
"""This code contains the code for the forwarder agent"""
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from typing_extensions import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage , ToolMessage , HumanMessage, AIMessage, get_buffer_string
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.prompt import missing_mandatory_fields_prompt, missing_optional_fields_prompt, \
                        user_confirmation_prompt, forwarder_agent_tasks
from src.forwarder_schema import ForwarderSchema , ForwarderState
from src.ibl_data_source import ibl_data_source

# Load environment variables
load_dotenv()

# Current Date
def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %#d, %Y")

# ===== Import forwarder Fields ("Mandatory","Optional") =====
import_forwarder_schema = ibl_data_source("../IBL_SCHEMA.json","forwarder_agent")

forwarder_fields = [
    item for item in import_forwarder_schema
]
mandatory_fields = [
    item['field'] for item in import_forwarder_schema if item.get('required') is True
]
optional_fields = [
    item['field'] for item in import_forwarder_schema if item.get('required') is False
]

def get_selected_field_details(all_fields, missed_fields):
    """
    """

    return [ fields for fields in all_fields if fields['field'] in missed_fields]

# ===== MCP Configuration =====
mcp_config = None

try:
    with open ("../mcp_servers.json" , "r") as mcp_file:
        mcp_config = json.load(mcp_file)
except FileNotFoundError:
    print("Error: mcp_servers.json not found. Please create it.")
    exit()

# Global client variable - will be initialized lazily
_client = None

def get_mcp_client():
    """Get or initialize MCP client lazily to avoid issues with LangGraph Platform."""
    global _client
    if _client is None:
        _client = MultiServerMCPClient(mcp_config)
    return _client

# Initialize model
model = init_chat_model(model="openai:gpt-4.1", temperature=0.0)
summarize_model = model

def forwarder_agent(state: ForwarderState) -> Command[Literal["forwarder_tools", "ConfirmWithUser", "CommitForwarderTransaction" , "__end__"]]:
    """
       Forwarder Agent assesses whether the received data is adequate to make deterministic decisions 
       about committing the data to the forwarder database.
    """
    # Set up structured output model
    structured_output_model = model.with_structured_output(ForwarderSchema)

    # Invoke the model
    response = structured_output_model.invoke([
               HumanMessage(content = forwarder_agent_tasks.format(
                                      agent_brief = state["agent_brief"], 
                                      date = get_today_str(),
                                      fields_details = forwarder_fields,
                                      mandatory_fields = mandatory_fields,
                                      optional_fields = optional_fields
               ))
    ])

    agent_brief_messages = [AIMessage(content = state["agent_brief"])]

    if response.missing_mandatory_fields:        # missing mandatory fields
        return Command(
               goto=END, 
               update={"messages": agent_brief_messages + [model.invoke([AIMessage(content = missing_mandatory_fields_prompt.format(
                                                                                   agent = "Forwarder" ,
                                                                                   missing_mandatory_fields = response.missing_mandatory_fields,
                                                                                   missing_mandatory_field_details = get_selected_field_details(all_fields = forwarder_fields,
                                                                                                                                                missed_fields = response.missing_mandatory_fields))
                                                     )])]}
        )
    elif response.missing_optional_fields and response.ask_for_optional_fields: # missing optional fields before confirmation
        return Command(
               goto=END, 
               update={"messages": agent_brief_messages + [model.invoke([AIMessage(content = missing_optional_fields_prompt.format(
                                                                                   agent = "Forwarder" ,
                                                                                   missing_optional_fields = response.missing_optional_fields,
                                                                                   missing_optional_field_details = get_selected_field_details(all_fields = forwarder_fields,
                                                                                                                                               missed_fields = response.missing_optional_fields))
                                                     )])]}
        )
    elif response.needs_user_confirmation: # missing confirmation
        return Command(
               goto = "ConfirmWithUser", 
               update = {"agent_response" : response,
                          "messages" : agent_brief_messages}
        )
    else: # everything is OK and confirmed
        return Command(
               goto = "CommitForwarderTransaction", 
               update = {"agent_response": response , 
                         "messages" : agent_brief_messages}
        )

def ConfirmWithUser(state: ForwarderState) -> Command[Literal["__end__"]]: 
    """ If there is anything that Forwarder Agent needs to confirm with the user """
    # first summarize 
    # system_message = summarize_logistics_system_prompt.format(date=get_today_str())
    # messages = [SystemMessage(content=system_message)] + state.get("messages", []) + [HumanMessage(content=summarize_logistics_human_prompt)]
    # response = summarize_model.invoke(messages)
    # Print the summary requesting confirmation
    return Command(
           goto=END, 
           update={"messages": model.invoke([AIMessage(content = user_confirmation_prompt.format(agent = "Forwarder" , information_report = state["agent_response"].model_dump()))])}
    )

def forwarder_tools(state: ForwarderState):
    """
        Executes all tool calls from the forwarder Agent response.
        Returns updated state with tool execution results.
    """
    tool_calls = state["supervisor_messages"][-1].tool_calls

    tools =  []
    tools_by_name = {}

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

async def CommitForwarderTransaction(state: ForwarderState):
    """ Following the user's confirmation, the forwarder database will be updated with the received data """

    # Get available tools from MCP server
    client = get_mcp_client()
    tools = await client.get_tools()
    tools_by_name = {tool.name: tool for tool in tools}

    # Get the update database tool
    UpdateDB = tools_by_name["UpdateDB"]

    # Initialize model with tool binding
    # model_with_tools = model.bind_tools(UpdateDB)

    # get the last response which includes all the filled values after confirmation
    response = state["agent_response"]

    # Convert the response into dictionary and delete unnecessary fields
    response_dict = response.model_dump()
    shipment_only = {k:v for (k,v) in response_dict.items() if k not in ["missing_mandatory_fields", "missing_optional_fields",
                                                                         "ask_for_optional_fields", "needs_user_confirmation"]}
    # commit the forwarder transactions following the confirmation
    confirmation_result = await UpdateDB.ainvoke({"record": shipment_only['shipment']})

    return{
            "messages": [AIMessage(content=f"{confirmation_result}")]     # confirm back
    }

# Build the scoping workflow
forwarder_agent_builder = StateGraph(ForwarderState)

# Add workflow nodes
forwarder_agent_builder.add_node("forwarder_agent", forwarder_agent)
forwarder_agent_builder.add_node("forwarder_tools", forwarder_tools)
forwarder_agent_builder.add_node("ConfirmWithUser", ConfirmWithUser)
forwarder_agent_builder.add_node("CommitForwarderTransaction", CommitForwarderTransaction)

# Add workflow edges
forwarder_agent_builder.add_edge(START, "forwarder_agent")
forwarder_agent_builder.add_edge("forwarder_tools", "forwarder_agent")
forwarder_agent_builder.add_edge("ConfirmWithUser", END)
forwarder_agent_builder.add_edge("CommitForwarderTransaction", END)

# Compile the workflow
checkpointer = InMemorySaver()
ForwarderAgent = forwarder_agent_builder.compile(checkpointer = checkpointer)
