# filename: main.py
from fastapi import FastAPI
from pydantic import BaseModel
from src.utils import format_message
from langchain_core.messages import HumanMessage
from src.full_agent import full_agent

# Define the request body schemaad
class UserRequest(BaseModel):
      usermessage: str
      username: str

# Initialize FastAPI app
app = FastAPI()

# Define the POST endpoint
@app.post("/submit-message")
async def submit_message(request: UserRequest):
    thread = {"configurable":{"thread_id":request.username}}
    result = await full_agent.ainvoke({"messages":[HumanMessage(content=request.usermessage)]} , config=thread)
    return {"message": result["messages"]}