from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from services import ai_wrapper
from services.prompts import MAIN_LLM_SYSTEM

router = APIRouter(prefix="/api/chat", tags=["chat"])

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    notebooks: Optional[List[str]] = []

class ChatCompletionResponse(BaseModel):
    response: str
    prefetch_content: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

@router.post("/completion", response_model=ChatCompletionResponse)
async def chat_completion(request: ChatCompletionRequest):
    """
    Stateless chat completion endpoint.
    Takes a list of messages and returns the AI response along with prefetch content.
    """
    try:
        # Convert Pydantic models to dicts for the service
        messages_dict = [msg.model_dump() for msg in request.messages]
        print(messages_dict)
        # We need to manage keywords for prefetch context, but since it's stateless, 
        # we'll start fresh or maybe we could accept them from frontend if we wanted persistence in session.
        # For now, let's assume fresh keywords for each request or just pass empty list 
        # and let the service handle it (it updates the list in place).
        keywords = [] 
        
        # Execute chat
        # execute_chat returns (new_messages, execution_logs)
        # new_messages includes the assistant response
        system = [{"role": "system", "content": MAIN_LLM_SYSTEM.format(notebook_summary = ai_wrapper.summarize_notebooks(request.notebooks))}]
        new_messages, execution_logs = ai_wrapper.execute_chat(
            system + messages_dict, 
            keywords, 
            request.notebooks
        )
        
        # Extract the assistant's response
        assistant_response = ""
        if new_messages and new_messages[-1]["role"] == "assistant":
            assistant_response = new_messages[-1]["content"]
            
        # Extract prefetch content from logs
        prefetch_content = execution_logs.get("prefetch", {})
        
        # Extract tool calls from main_llm logs
        tool_calls = []
        main_llm_logs = execution_logs.get("main_llm", [])
        for log in main_llm_logs:
            if "tool_calls" in log:
                tool_calls.extend(log["tool_calls"])
        
        return ChatCompletionResponse(
            response=assistant_response,
            prefetch_content=prefetch_content,
            tool_calls=tool_calls
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
