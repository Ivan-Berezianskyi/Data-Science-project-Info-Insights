import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import numpy as np

def compare_runs(baseline_file, optimized_file):
    if not os.path.exists(baseline_file) or not os.path.exists(optimized_file):
        print(f"Error: Files not found.")
        return

    print(f"Comparing:\n 1. {baseline_file}\n 2. {optimized_file}")
    
    df_base = pd.read_csv(baseline_file)
    df_opt = pd.read_csv(optimized_file)

    metrics = ['context_precision', 'context_recall', 'faithfulness', 'answer_relevancy']
    results = []
    
    for metric in metrics:
        if metric in df_base.columns and metric in df_opt.columns:
            val_base = df_base[metric].mean()
            val_opt = df_opt[metric].mean()
            
            if val_base == 0:
                diff_pct = 100.0 if val_opt > 0 else 0.0
            else:
                diff_pct = ((val_opt - val_base) / val_base) * 100

            results.append({
                "Metric": metric.replace('_', ' ').title(),
                "Baseline": val_base,
                "Optimized": val_opt,
                "Improvement": diff_pct
            })

    df_comparison = pd.DataFrame(results)

    print("\n" + "="*80)
    print("FINAL REALISTIC A/B TEST REPORT")
    print("="*80)
    print(f"{'METRIC':<25} | {'BASE':<8} | {'OPT':<8} | {'CHANGE':<15}")
    print("-" * 70)
    
    for _, row in df_comparison.iterrows():
        diff = row['Improvement']
        color = "\033[92m" if diff > 0 else ("\033[91m" if diff < 0 else "")
        reset = "\033[0m"
        print(f"{row['Metric']:<25} | {row['Baseline']:.4f}   | {row['Optimized']:.4f}   | {color}{diff:+.2f}%{reset}")
    print("="*80 + "\n")

    generate_chart(df_comparison)
    df_comparison.to_csv("final_comparison_report.csv", index=False)

def generate_chart(df):
    try:
        labels = df['Metric']
        x = np.arange(len(labels))
        width = 0.35

        fig, ax = plt.subplots(figsize=(12, 7))
        rects1 = ax.bar(x - width/2, df['Baseline'], width, label='Raw Search (Prod Sim)', color='#d62728', alpha=0.7)
        rects2 = ax.bar(x + width/2, df['Optimized'], width, label='Prefetch (Prod Sim)', color='#2ca02c', alpha=0.9)

        ax.set_ylabel('Score (0.0 - 1.0)')
        ax.set_title('Production Simulation: Raw vs Prefetch (GPT-3.5 + Limit 5)')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend(loc='lower right')
        ax.set_ylim(0, 1.15)

        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height*100:.1f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=10, fontweight='bold')

        autolabel(rects1)
        autolabel(rects2)

        fig.tight_layout()
        plt.savefig('comparison_chart.png')
        print("Chart saved to: comparison_chart.png 📊")
    except Exception as e:
        print(f"Chart error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        compare_runs(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python compare_results.py <baseline.csv> <optimized.csv>")