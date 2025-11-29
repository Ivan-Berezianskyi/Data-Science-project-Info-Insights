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

from services.ai_wrapper import execute_chat, summarize_notebooks
from services.rag import rag_service
from services.prompts import MAIN_LLM_SYSTEM, PRE_FETCH_LLM, PRE_FETCH_LLM_USER

# === НАЛАШТУВАННЯ ЯК НА ПРОДАКШНІ ===
PRODUCTION_MODEL = "gpt-3.5-turbo"
PRODUCTION_LIMIT = 5
# ====================================

def load_test_data(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def emulate_production_prefetch(question: str, notebook_id: str, llm) -> str:
    """
    Повна імітація логіки prefetch з ai_wrapper.py:
    1. Пошук (Raw)
    2. Аналіз через GPT-3.5 (використовуючи REAL prompts)
    3. Витягування search_keywords
    """
    # 1. Початковий "грубий" пошук (як в prefetch функції)
    try:
        initial_context = rag_service.search_data(notebook_id, question, limit=PRODUCTION_LIMIT)
    except Exception:
        return ""

    if not initial_context:
        return ""

    # 2. Формування промпта (ТОЧНО як в ai_wrapper.py)
    messages = [
        {"role": "system", "content": PRE_FETCH_LLM},
        {
            "role": "user", 
            "content": PRE_FETCH_LLM_USER.format(
                user_query=question, 
                result=json.dumps(initial_context)
            )
        }
    ]

    # 3. Виклик LLM
    try:
        response = llm.invoke(messages)
        content = response.content
        
        # 4. Спроба розпарсити JSON (спрощена, без json_repair щоб не тягнути зайві ліби, але надійна)
        # Шукаємо початок JSON об'єкта
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            data = json.loads(json_str)
            keywords = data.get("search_keywords", [])
            return " ".join(keywords)
    except Exception as e:
        print(f"   [Warning] Prefetch JSON parse error: {e}")
        return ""
    
    return ""

def run_rag_query(question: str, notebooks: List[str], mode: str) -> Dict[str, Any]:
    # Використовуємо GPT-3.5 (Realism)
    llm = ChatOpenAI(model=PRODUCTION_MODEL, temperature=0)
    
    search_keywords_map = {} # Зберігаємо ключі для кожного нотбука окремо
    
    # --- ЛОГІКА ПОШУКУ ---
    if mode == "prefetch":
        print(f"   [Mode: PREFETCH (Prod Sim)] Analyzing...")
        # Для кожного нотбука генеруємо свої ключі (як в ai_wrapper)
        for nb in notebooks:
            keys = emulate_production_prefetch(question, nb, llm)
            search_keywords_map[nb] = keys
            if keys:
                print(f"      └─ [{nb}] Keys: {keys}")
    else:
        print(f"   [Mode: RAW] Using raw question")
    # ---------------------

    # 1. Виклик Бота (Execute Chat)
    # Збираємо всі ключі в один список для бота
    all_keywords_list = list(filter(None, search_keywords_map.values()))
    
    notebook_summary = summarize_notebooks(notebooks)
    messages = [
        {"role": "system", "content": MAIN_LLM_SYSTEM.format(notebook_summary=notebook_summary)},
        {"role": "user", "content": question}
    ]
    
    # Бот отримує ключі, щоб сформувати відповідь
    response_messages = execute_chat(messages, all_keywords_list, notebooks)
    answer = response_messages[-1]["content"] if response_messages else ""
    
    # 2. Збір Контексту для RAGAS
    # Тут ми емулюємо "Final Search" з prefetch()
    all_contexts = []
    
    for notebook in notebooks:
        try:
            if mode == "prefetch":
                keys = search_keywords_map.get(notebook, "")
                # ЛОГІКА ПРОДАКШНУ: "query + keywords"
                final_query = f"{question} {keys}".strip()
            else:
                final_query = question

            # PRODUCTION LIMIT (5)
            contexts = rag_service.search_data(notebook, final_query, limit=PRODUCTION_LIMIT)
            all_contexts.extend([ctx["text"] for ctx in contexts])
            
        except Exception as e:
            print(f"   [Warning] Error searching '{notebook}': {e}")
            all_contexts.append("")

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
    parser.add_argument("--notebooks", nargs="+", default=["nasa", "spacex"])
    parser.add_argument("--output", type=str, default="ragas_results.csv")
    parser.add_argument("--mode", choices=["prefetch", "raw"], default="prefetch")
    
    args = parser.parse_args()
    
    test_data = load_test_data(args.test_data)
    dataset = prepare_ragas_dataset(test_data, args.notebooks, args.mode)
    evaluate_with_ragas(dataset, args.output)

if __name__ == "__main__":
    main()