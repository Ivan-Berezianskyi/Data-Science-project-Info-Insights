import json
import argparse
import os
import sys
import random
import subprocess
from typing import List

sys.path.append(os.getcwd())

from services.rag import rag_service
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def generate_tricky_questions(notebook_id: str, num_questions: int, output_file: str):
    print(f"\n🔹 ЕТАП 1: Генерація 'хитрих' питань з '{notebook_id}'...")
    try:
        texts = rag_service.scroll_notebook(notebook_id, limit=200)
        if not texts:
            print("❌ Нотбук порожній.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Помилка бази: {e}")
        sys.exit(1)

    llm = ChatOpenAI(model="gpt-4o", temperature=0.8)
    dataset = []

    for i in range(num_questions):
        text_chunk = random.choice(texts)
        prompt = f"""
        Ти складаєш екзамен з дисципліни.
        Створи 1 складне питання до тексту.
        
        ВАЖЛИВО:
        1. Використовуй синоніми та описи, НЕ використовуй прямі цитати.
        2. Питання має бути зрозумілим людині, але важким для пошуку за ключовими словами.
        
        Текст: "{text_chunk[:1000]}"
        
        Виведи JSON: {{ "question": "...", "ground_truth": "..." }}
        """
        
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            dataset.append({
                "question": data["question"],
                "ground_truth": data["ground_truth"],
                "notebooks": [notebook_id]
            })
            print(f"   ✅ Питання {i+1} згенеровано.")
        except:
            print(f"   ⚠️ Пропуск.")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)
    print(f"   Збережено: {output_file}")

def run_full_ab_test(notebook_id: str, count: int):
    test_file = f"test_data_{notebook_id}.json"
    base_csv = f"results_baseline_{notebook_id}.csv"
    opt_csv = f"results_optimized_{notebook_id}.csv"
    
    generate_tricky_questions(notebook_id, count, test_file)
    
    print("\n🚀 Запуск Mode: RAW (Baseline)...")
    subprocess.run([sys.executable, "evaluate_ragas.py", "--test-data", test_file, "--notebooks", notebook_id, "--mode", "raw", "--output", base_csv])

    print("\n🚀 Запуск Mode: PREFETCH (Optimized)...")
    subprocess.run([sys.executable, "evaluate_ragas.py", "--test-data", test_file, "--notebooks", notebook_id, "--mode", "prefetch", "--output", opt_csv])

    print("\n🔹 ЕТАП 3: Підсумки...")
    subprocess.run([sys.executable, "compare_results.py", base_csv, opt_csv])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebook", type=str, default="discrete_math")
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()
    run_full_ab_test(args.notebook, args.count)