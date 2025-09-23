# filename: main.py
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from src.full_agent import full_agent

# Define the request body schemaad
class UserRequest(BaseModel):
      usermessage : str
      username : str

# Initialize FastAPI app
app = FastAPI()

# Define the POST endpoint
@app.post("/submit-message")
async def submit_message(request: UserRequest):
    thread = {"configurable":{"thread_id":request.username}}
    result = await full_agent.ainvoke({"messages":[HumanMessage(content=request.usermessage)]} , config=thread)
    return {"message": result["messages"]}

if __name__ == "__main__":
     uvicorn.run(app, host="127.0.0.1", port=8000)