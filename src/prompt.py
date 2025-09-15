"""Prompt templates for the Inbound Logistics system.

This module contains all prompt templates used across the Inbound Logistics workflow components
"""

decision_to_route_inbound_logistics_tasks = """
These are the inbound logistics Data received so far:
<Data>
{message}
</Data>

Today's date is {date}.

Your role is to act as the Supervisor Agent in the Inbound Logistics system.  
Your responsibilities are:
1. Assess the data provided by the user.  
2. Decide whether the task should be delegated to:
   - `logistician_agent` → if the request relates to AWB# or AWB Date.  
   - `clearance_agent` → if the request relates to ATA or Clearance Date.  
3. If the request is ambiguous or missing critical details, ask the user a **clarifying question** before assigning the task.  

Guidelines for asking clarification:
- Only ask if **absolutely necessary** (e.g., AWB#).  
- Keep questions **concise and structured**. Use bullet points or lists if multiple clarifications are needed.  
- Do not repeat questions if the information is already provided.  

Respond in **valid JSON format** with these exact keys:
- `"question"`: "<clarifying question used with <delegate_to=clarify_with_user> if necessary information is needed, otherwise empty>"  
- `"delegate_to"`: "logistician_agent" | "clearance_agent" | "supervisor_tools" | "clarify_with_user"  
- `"agent_brief"`: "<acknowledgement message briefing the task sent to the chosen agent, confirming the assignment>"  

Behavior:
- If clarification is needed → return: 
  - `"question": "<your clarifying question>"`  
  - `"delegate_to": "clarify_with_user"`  
  - `"agent_brief": ""`  

- If no clarification is needed → return: 
  - `"question": ""`  
  - `"delegate_to": "<the chosen agent other than clarify_with_user>"`  
  - `"agent_brief": "<acknowledgement message confirming the task assignment and briefly summarizing the understood request>"`  

Keep the verification message professional and concise, e.g.,  
- `"Based on the provided details, I will assign this task to the Clearance Agent for customs clearance."`  
- `"Your request relates to AWB#, so I will assign it to the Logistician Agent for further handling."

"""

logistics_prompt = """ """
missing_mandatory_fields_prompt = """ """
missing_optional_fields_prompt = """ """
logistics_confirmation_prompt = """ """
summarize_logistics_system_prompt = """ """ # ref compress_research_system_prompt
summarize_logistics_human_prompt = """ """  # ref compress_research_human_message
clearing_prompt = """ """