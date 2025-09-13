"""Prompt templates for the Inbound Logistics system.

This module contains all prompt templates used across the Inbound Logistics workflow components
"""


decision_to_route_inbound_logistics_tasks = """
These are the inbound logistics Data received so far:
<Data>
{data}
</Data>

Today's date is {date}.

Your role is to act as the Supervisor Agent in the Inbound Logistics system.  
Your responsibilities are:
1. Assess the data provided by the user.  
2. Decide whether the task should be delegated to:
   - Logistician Agent → if the request relates to AWB# or AWB Date.  
   - Clearance Agent → if the request relates to ATA or Clearance Date.  
3. If the request is ambiguous or missing critical details, ask the user a **clarifying question** before assigning the task.  

Guidelines for asking clarification:
- Only ask if **absolutely necessary** (e.g., AWB#).  
- Keep questions **concise and structured**. Use bullet points or lists if multiple clarifications are needed.  
- Do not repeat questions if the information is already provided.  

Respond in **valid JSON format** with these exact keys:
- `"need_clarification"`: boolean  
- `"question"`: "<clarifying question if more information is needed, otherwise empty>"  
- `"delegate_to"`: "Logistician Agent" | "Clearance Agent" | ""  
- `"verification"`: "<acknowledgement message confirming the assignment or clarification>"  

Behavior:
- If clarification is needed → return:  
  - `"need_clarification": true`  
  - `"question": "<your clarifying question>"`  
  - `"delegate_to": ""`  
  - `"verification": ""`  

- If no clarification is needed → return:  
  - `"need_clarification": false`  
  - `"question": ""`  
  - `"delegate_to": "<the chosen agent>"`  
  - `"verification": "<acknowledgement message confirming the task assignment and briefly summarizing the understood request>"`  

Keep the verification message professional and concise, e.g.,  
- `"Based on the provided details, I will assign this task to the Clearance Agent for customs clearance."`  
- `"Your request relates to AWB#, so I will assign it to the Logistician Agent for further handling."

"""