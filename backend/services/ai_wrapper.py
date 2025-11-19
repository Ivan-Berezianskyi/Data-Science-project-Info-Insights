from services.groq_service import client
from services.rag import rag_service
import json
MAIN_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
SUMMARY_MODEL = "llama-3.1-8b-instant"

def search_data(query):
    print(query)
    res = []
    try:
        res.append(json.dumps(rag_service.search_data("test",query)))
        return json.dumps({"result" :res})
    except Exception as e:
        return json.dumps({"error" : e})

tools_schema = {
    "type": "function",
    "function": {
        "name": "search_data",
        "description": "Search for data in the RAG database.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to search for data in the RAG database. Select them based on missing knowledge"
                }
            }
        },
        "required": ["query"]
    }
}

def execute_chat(messages: list[dict]):
    new_messages = []
    response = client.chat.completions.create(
        model=MAIN_MODEL,
        messages=messages,
        stream=False,
        tools=[tools_schema],
        tool_choice="auto",
        max_completion_tokens=4096
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    new_messages.append({"role" : "assistant", "content" : response_message.content})
    if tool_calls:
        available_functions = {
            "search_data": search_data,
        }
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                query=function_args.get("query")
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id, 
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
            new_messages.append(                {
                    "tool_call_id": tool_call.id, 
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
        second_response = client.chat.completions.create(
            model=MAIN_MODEL,
            messages=messages
        )
        new_messages.append({"role" : "assistant", "content" : second_response.choices[0].message.content})
    return new_messages