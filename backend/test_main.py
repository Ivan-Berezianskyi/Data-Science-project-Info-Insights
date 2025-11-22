from services.prompts import MAIN_LLM_SYSTEM
from services.rag import rag_service
from services.ai_wrapper import execute_chat, summarize_notebooks

notebooks=["nasa", "spacex"]
messages = [{"role": "system", "content": MAIN_LLM_SYSTEM.format(notebook_summary = summarize_notebooks(notebooks))}]
keywords = []
while True:
    inp = input()
    messages.append({
        "role" : "user",
        "content": inp
    })
    res = execute_chat(messages, keywords, notebooks)
    print(keywords)
    print("\n### RESPONSE\n{data}\n".format(data=res[-1]["content"]))
    for message in res:
        messages.append(message)
