import json
from services.prompts import MAIN_LLM_SYSTEM
from services.rag import rag_service
from services.ai_wrapper import execute_chat, summarize_notebooks

questions = [
    "What is a tautology, and how is it different from a contradiction?",
    "State the Inclusion-Exclusion Principle for three sets A, B, and C.",
    "According to Euler's Theorem, what is the necessary and sufficient condition for a connected graph to contain an Eulerian cycle?",
    "State Euler's formula for a connected planar graph relating the number of vertices (n), edges (m), and faces (r)",
    "Describe the main steps of Dijkstra's algorithm for finding the shortest path in a weighted graph.",
    "What is the difference between Prim's algorithm and Kruskal's algorithm for finding the Minimum Spanning Tree (MST)?",
    "List the three principles of vertex ordering (traversal) in a binary tree (preorder, inorder, postorder).",
    "Define an AVL tree and explain the condition regarding the height of its subtrees.",
    "Define reflexive, symmetric, and transitive relations.",
    "What conditions must a function satisfy to be called a bijection (bijective function)?",
    "How are Karnaugh maps used to find the minimal Disjunctive Normal Form (DNF) of a Boolean function?",
    "What is a Hamming code, and how is the redundancy of a code calculated?",
]

def run_tests():
    notebooks = ["discrete_math"]
    notebook_summary = summarize_notebooks(notebooks)
    system_prompt = MAIN_LLM_SYSTEM.format(notebook_summary=notebook_summary)
    
    results = []
    
    for q in questions:
        print(f"Running test for: {q}")
        messages = [{"role": "system", "content": system_prompt}]
        keywords = []
        
        messages.append({"role": "user", "content": q})
        
        response_messages, logs = execute_chat(messages, keywords, notebooks)
            
        final_response = response_messages[-1]["content"]
        print(list(map(lambda x: x["tool_calls"], logs["main_llm"])))
        tool_outputs = []
        for turn in logs["main_llm"]:
            for tool_call in turn.get("tool_calls", []):
                tool_outputs.append(tool_call["response"])
        
        input_data = {
            "initial_prompt": logs["input"],
            "tool_outputs": tool_outputs
        }

        test_result = {
                "question": q,
                "response": final_response,
                "input": input_data,
                "total_input_tokens": sum(x.get("input_tokens", 0) for x in logs["prefetch"]["notebooks"]),
                "total_output_tokens": sum(x.get("output_tokens", 0) for x in logs["prefetch"]["notebooks"]) + logs["tool_tokens"]
            }
        results.append(test_result)
        print(f"Completed: {q}")
            


    with open("rag_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("Tests completed. Results saved to rag_test_results.json")

if __name__ == "__main__":
    run_tests()