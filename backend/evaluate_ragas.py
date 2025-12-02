#!/usr/bin/env python3
import json
import argparse
import os
import sys
from typing import List, Dict, Any
import pandas as pd
from datasets import Dataset

# --- Imports for RAGAS and OpenAI ---
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# --- Local Service Imports ---
sys.path.append(os.getcwd())

from services.ai_wrapper import execute_chat, summarize_notebooks, prefetch
from services.rag import rag_service
from services.prompts import MAIN_LLM_SYSTEM

# === НАЛАШТУВАННЯ ЯК НА ПРОДАКШНІ ===
PRODUCTION_MODEL = "gpt-3.5-turbo"
PRODUCTION_LIMIT = 5
# ====================================

def load_test_data(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_rag_query(question: str, notebooks: List[str], mode: str) -> Dict[str, Any]:
    """
    Run a RAG query using the actual ai_wrapper functions.
    """
    keywords = []
    
    # 1. Виклик Бота (Execute Chat)
    notebook_summary = summarize_notebooks(notebooks)
    messages = [
        {"role": "system", "content": MAIN_LLM_SYSTEM.format(notebook_summary=notebook_summary)},
        {"role": "user", "content": question}
    ]
    
    print(f"   [Execute Chat] Running pipeline for: {question[:50]}...")
    
    # Бот отримує ключі, щоб сформувати відповідь
    # execute_chat handles prefetch internally based on mode
    prefetch_enabled = (mode == "prefetch")
    new_messages, execution_logs = execute_chat(messages, keywords, notebooks, prefetch_enabled=prefetch_enabled)
    
    answer = ""
    if new_messages:
        answer = new_messages[-1]["content"]
    
    # 2. Збір Контексту з логів виконання (Context Retrieval from Execution Logs)
    all_contexts = []
    
    # Extract contexts from tool calls in main_llm logs
    if "main_llm" in execution_logs:
        for turn in execution_logs["main_llm"]:
            if "tool_calls" in turn:
                for tool_call in turn["tool_calls"]:
                    if tool_call["name"] == "search_data" and tool_call.get("response"):
                        try:
                            # Parse the double-encoded JSON response
                            # response is string: '{"result": ["[{...}]"]}'
                            response_obj = json.loads(tool_call["response"])
                            result_list = response_obj.get("result", [])
                            
                            for result_str in result_list:
                                # result_str is string: '[{...}]'
                                items = json.loads(result_str)
                                for item in items:
                                    if isinstance(item, dict) and "text" in item:
                                        all_contexts.append(item["text"])
                        except Exception as e:
                            print(f"   [Warning] Error parsing tool response: {e}")

    return {
        "answer": answer,
        "contexts": all_contexts,
        "retrieved_contexts": all_contexts
    }

def prepare_ragas_dataset(test_data: List[Dict[str, Any]], notebooks: List[str], mode: str) -> Dataset:
    results = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
    
    print(f"Running {len(test_data)} queries (Mode: {mode.upper()})...")
    
    for i, test_case in enumerate(test_data, 1):
        question = test_case["question"]
        ground_truth = test_case.get("ground_truth", "")
        test_notebooks = test_case.get("notebooks", notebooks)
        
        print(f"[{i}/{len(test_data)}] Processing: {question[:50]}...")
        rag_result = run_rag_query(question, test_notebooks, mode)
        
        contexts = rag_result["contexts"] if rag_result["contexts"] else ["No context found"]
        
        results["question"].append(question)
        results["answer"].append(rag_result["answer"])
        results["contexts"].append(contexts)
        results["ground_truth"].append(ground_truth)
    
    return Dataset.from_dict(results)

def evaluate_with_ragas(dataset: Dataset, output_file: str) -> pd.DataFrame:
    print("\nEvaluating with RAGAS metrics...")
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    
    # Суддя - GPT-4o (Він має бути розумним, щоб оцінити GPT-3.5)
    judge_llm = ChatOpenAI(model="gpt-4o") 
    judge_embeddings = OpenAIEmbeddings()

    try:
        result = evaluate(dataset=dataset, metrics=metrics, llm=judge_llm, embeddings=judge_embeddings)
        
        if hasattr(result, 'to_pandas'):
            df = result.to_pandas()
        elif isinstance(result, dict):
            df = pd.DataFrame(result)
        else:
            df = pd.DataFrame(dict(result))
            
    except Exception as e:
        print(f"Error during evaluation: {e}")
        raise
    
    if output_file:
        df.to_csv(output_file, index=False)
        print(f"\nResults saved to: {output_file}")
    
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-data", type=str, required=True)
    parser.add_argument("--notebooks", nargs="+", default=["discrete_math"])
    parser.add_argument("--output", type=str, default="ragas_results.csv")
    parser.add_argument("--mode", choices=["prefetch", "raw"], default="prefetch")
    
    args = parser.parse_args()
    
    test_data = load_test_data(args.test_data)
    dataset = prepare_ragas_dataset(test_data, args.notebooks, args.mode)
    evaluate_with_ragas(dataset, args.output)

if __name__ == "__main__":
    main()