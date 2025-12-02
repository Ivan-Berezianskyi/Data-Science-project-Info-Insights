from services.openai_service import client
from services.rag import rag_service
from services.prompts import (
    MAIN_LLM_USER,
    PRE_FETCH_LLM,
    PRE_FETCH_LLM_USER,
    SUMMARY_MODEL_PROMT,
    SEARCH_QUERY_OPTIMIZER,
    SEARCH_QUERY_OPTIMIZER_USER,
)
import json
import json_repair
import tiktoken

MAIN_MODEL = "gpt-4o"
PREFETCH_MODEL = "gpt-3.5-turbo"


def search_data(notebook: str, query: str, count: int = 5):
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
    refinement_messages = [
        {"role": "system", "content": SEARCH_QUERY_OPTIMIZER},
        {
            "role": "user", 
            "content": SEARCH_QUERY_OPTIMIZER_USER.format(
                user_query=query, 
                keywords=", ".join(keywords) if keywords else "None"
            )
        }
    ]
    
    try:
        refinement_response = client.chat.completions.create(
            model=PREFETCH_MODEL, 
            messages=refinement_messages, 
            temperature=0
        )
        refined_query = refinement_response.choices[0].message.content.strip()
        print(f"Refined Query: {refined_query}")
    except Exception as e:
        print(f"Error refining query: {e}")
        refined_query = query

    logs = {
        "refined_query": refined_query,
        "notebooks": []
    }

    output = []
    for notebook in notebooks:
        rag_data = rag_service.search_data(notebook, refined_query, 10)
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
        
        notebook_log = {
            "notebook": notebook,
            "raw_response": content,
            "rag_data_count": len(rag_data)
        }
        
        notebook_log["input_tokens"] = response.usage.prompt_tokens
        notebook_log["output_tokens"] = response.usage.completion_tokens
        
        try:
            res = json_repair.loads(content)
            response_data = res.get("suggested_search_keywords", [])
            keywords[:] = response_data
            if "suggested_search_keywords" in res:
                res.pop("suggested_search_keywords")
            
            output.append({"notebook": notebook, "data": res})
            notebook_log["parsed_data"] = res
            notebook_log["status"] = "success"
        except Exception as e:
            print(f"Error parsing response: {e}")
            output.append(
                {"notebook": notebook, "data": {"score": "ERROR", "extracted_facts": []}}
            )
            notebook_log["status"] = "error"
            notebook_log["error"] = str(e)
            
        logs["notebooks"].append(notebook_log)
            
    return output, logs

def summarize_notebooks(notebooks: list[str]):
    output = ""
    for notebook in notebooks:
        rag_data = rag_service.scroll_notebook(notebook, 5);
        response = client.chat.completions.create(
            model=PREFETCH_MODEL, messages=[{"role" : "system", "content": SUMMARY_MODEL_PROMT}, {"role" : "user", "content": json.dumps(rag_data)}], temperature=0
        )
        output += f" - {notebook}: {response.choices[0].message.content}\n"
    return output


def execute_chat(messages: list[dict], keywords: list[str], notebooks: list[str], prefetch_enabled: bool = True):
    execution_logs = {
        "prefetch": {},
        "main_llm": []
    }
    new_messages = []
    
    if prefetch_enabled:
        prefetch_res, prefetch_logs = prefetch(messages[-1]["content"], keywords, notebooks)
        execution_logs["prefetch"] = prefetch_logs
    else:
        prefetch_res = []
        execution_logs["prefetch"] = {}
    
    encoding = tiktoken.get_encoding("cl100k_base")
    execution_logs["prefetch_content_tokens"] = len(encoding.encode(str(prefetch_res)))
    
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
    execution_logs["input"] = formatted_last_msg

    to_send = [system_message] + history + [formatted_last_msg]

    response = client.chat.completions.create(
        model=MAIN_MODEL,
        messages=to_send,
        stream=False,
        tools=[tools_schema],
        tool_choice="auto",
    )
    execution_logs["tool_tokens"] = 0
    encoding = tiktoken.get_encoding("cl100k_base")
    
    while True:
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        to_send.append(response_message)
        
        # Log the assistant's turn
        turn_log = {
            "role": "assistant",
            "content": response_message.content,
            "tool_calls": []
        }
        
        if not tool_calls:
            # No tool calls = final response
            new_messages.append({"role": "assistant", "content": response_message.content})
            execution_logs["main_llm"].append(turn_log)
            return new_messages, execution_logs

        # Process tool calls
        print(f"Tool calls triggered: {len(tool_calls)}")
        
        available_functions = {
            "search_data": search_data,
        }

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions.get(function_name)
            
            tool_call_log = {
                "id": tool_call.id,
                "name": function_name,
                "arguments": tool_call.function.arguments,
                "response": None
            }
            
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

                tool_call_log["response"] = function_response
                
                to_send.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
            
            turn_log["tool_calls"].append(tool_call_log)
            execution_logs["tool_tokens"] += len(encoding.encode(function_response))

        execution_logs["main_llm"].append(turn_log)

        # Call LLM again with tool results
        response = client.chat.completions.create(
            model=MAIN_MODEL,
            messages=to_send,
            stream=False,
            tools=[tools_schema],
            tool_choice="auto",
        )
        # Loop continues to check if the new response has tool calls or is final
