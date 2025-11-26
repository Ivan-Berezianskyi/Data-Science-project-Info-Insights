from services.openai_service import client
from services.rag import rag_service
from services.prompts import (
    MAIN_LLM_USER,
    PRE_FETCH_LLM,
    PRE_FETCH_LLM_USER,
    SUMMARY_MODEL_PROMT,
)
import json
import json_repair

MAIN_MODEL = "gpt-4o"
PREFETCH_MODEL = "gpt-3.5-turbo"


def search_data(notebook: str, query: str, count: int = 8):
    print(f"\n\n**MAIN LLM SEARCH QUERY**: ({notebook}) {query}")
    res = []
    try:
        res.append(json.dumps(rag_service.search_data(notebook, query, count)))
        return json.dumps({"result": res})
    except Exception as e:
        return json.dumps({"error": str(e)})


tools_schema = {
    "type": "function",
    "function": {
        "name": "search_data",
        "description": "Search for data in the RAG database.",
        "parameters": {
            "type": "object",
            "properties": {
                "notebook": {
                    "type" : "string",
                    "description" : "Name of notebook where to execute query. Only use names provided in notebook_summary. Never use other names that isn't in notebook_summary"
                },
                "query": {
                    "type": "string",
                    "description": "The query to search for data in the RAG database. Select them based on missing knowledge",
                }
            },
        },
        "required": ["notebook","query"],
        "additionalProperties": False,
    },
    "strict": True,
}


def prefetch(query: str, keywords: list[str], notebooks: list[str]):
    output = []
    for notebook in notebooks:
        rag_data = rag_service.search_data(notebook, f"{query} {",".join(keywords)}", 5)
        messages = [
            {"role": "system", "content": PRE_FETCH_LLM},
            {
                "role": "user",
                "content": PRE_FETCH_LLM_USER.format(
                    user_query=query, result=json.dumps(rag_data)
                ),
            },
        ]
        response = client.chat.completions.create(
            model=PREFETCH_MODEL, messages=messages, temperature=0
        )
        content = response.choices[0].message.content
        print(
            """
### PREFETCH QUERY
{query}

### PREFETCH RESPONSE
{data}
        """.format(
                query=f"{query} {keywords}", data=content
            )
        )
        try:
            res = json_repair.loads(content)
            response_data = res["search_keywords"]
            keywords[:] = response_data
            res.pop("search_keywords")
            output.append({"notebook": notebook, "data": res})
        except:
            output.append(
                {"notebook": notebook, "data": {"score": "ERROR", "extracted_facts": []}}
            )
    return output

def summarize_notebooks(notebooks: list[str]):
    output = ""
    for notebook in notebooks:
        rag_data = rag_service.scroll_notebook(notebook, 5);
        response = client.chat.completions.create(
            model=PREFETCH_MODEL, messages=[{"role" : "system", "content": SUMMARY_MODEL_PROMT}, {"role" : "user", "content": json.dumps(rag_data)}], temperature=0
        )
        output += f" - {notebook}: {response.choices[0].message.content}\n"
    return output


def execute_chat(messages: list[dict], keywords: list[str], notebooks: list[str]):
    new_messages = []
    
    prefetch_res = prefetch(messages[-1]["content"], keywords, notebooks)
    print(prefetch_res)
    
    system_message = messages[0]
    history = messages[1:-1]
    last_user_content = messages[-1]["content"]

    formatted_last_msg = {
        "role": "user",
        "content": MAIN_LLM_USER.format(
            prefetch=prefetch_res,
            user=last_user_content,
        ),
    }

    to_send = [system_message] + history + [formatted_last_msg]

    response = client.chat.completions.create(
        model=MAIN_MODEL,
        messages=to_send,
        stream=False,
        tools=[tools_schema],
        tool_choice="auto",
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    to_send.append(response_message)
    
    if not tool_calls:
        new_messages.append({"role": "assistant", "content": response_message.content})
        return new_messages

    if tool_calls:
        print(f"Tool calls triggered: {len(tool_calls)}")
        
        available_functions = {
            "search_data": search_data,
        }

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions.get(function_name)
            
            if function_to_call:
                try:
                    function_args = json.loads(tool_call.function.arguments)
                    
                    function_response = function_to_call(
                        query=function_args.get("query"), 
                        notebook=function_args.get("notebook")
                    )
                except json.JSONDecodeError:
                    function_response = json.dumps({"error": "Invalid JSON arguments from model"})
                except Exception as e:
                    function_response = json.dumps({"error": str(e)})

                to_send.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )

        second_response = client.chat.completions.create(
            model=MAIN_MODEL, 
            messages=to_send
        )
        
        final_content = second_response.choices[0].message.content
        new_messages.append({"role": "assistant", "content": final_content})

    return new_messages
