from services.groq_service import client
from services.rag import rag_service
from services.prompts import MAIN_LLM_SYSTEM, MAIN_LLM_USER, PRE_FETCH_LLM, PRE_FETCH_LLM_USER
import json

MAIN_MODEL = "openai/gpt-oss-120b"
PREFETCH_MODEL = "llama-3.1-8b-instant"


def search_data(query: str, count: int = 5):
    print(f"\n\n**MAIN LLM SEARCH QUERY**:{query}")
    res = []
    try:
        res.append(json.dumps(rag_service.search_data("test", query, count)))
        return json.dumps({"result": res})
    except Exception as e:
        return json.dumps({"error": e})


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
                    "description": "The query to search for data in the RAG database. Select them based on missing knowledge",
                }
            },
        },
        "required": ["query"],
    },
}


def prefetch(query: str):
    rag_data = rag_service.search_data("test", query,3)
    messages = [{
        "role" : "system",
        "content" : PRE_FETCH_LLM
    }, {
        "role" : "user",
        "content": PRE_FETCH_LLM_USER.format(user_query=query, result= json.dumps(rag_data))
    }]
    response = client.chat.completions.create(
        model=PREFETCH_MODEL,
        messages=messages
    )
    print("""

### PREFETCH
{data}

    """.format(data=response.choices[0].message.content))
    return response.choices[0].message.content

def execute_chat(messages: list[dict]):

    new_messages = []
    to_send = [{"role": "system", "content": MAIN_LLM_SYSTEM}]+ messages[:-1] + [
            {
                "role": "user",
                "content": MAIN_LLM_USER.format(prefetch=prefetch(messages[-1]["content"]), user = messages[-1]["content"])
            }
        ]
    response = client.chat.completions.create(
        model=MAIN_MODEL,
        messages=to_send,
        stream=False,
        tools=[tools_schema],
        tool_choice="auto",
        max_completion_tokens=4096,
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    new_messages.append({"role": "assistant", "content": response_message.content})
    if tool_calls:
        available_functions = {
            "search_data": search_data,
        }
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(query=function_args.get("query"))
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
            new_messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
        second_response = client.chat.completions.create(
            model=MAIN_MODEL, messages=messages
        )
        new_messages.append(
            {"role": "assistant", "content": second_response.choices[0].message.content}
        )
    return new_messages
