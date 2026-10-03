import asyncio
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.gateway.adapters import kb

async def main():
    print("=== 1. KB PostgreSQL Health Check ===")
    h = await kb.check_kb_health()
    print("Health:", h)

    print("\n=== 2. Semantic Search: Gas Lock ===")
    res = await kb.search_kb("What is gas lock in ESP and how to prevent it?", top_k=3)
    print("Query:", res["query"])
    print("Total Hits:", len(res["hits"]))
    for i, hit in enumerate(res["hits"], 1):
        print(f"  Hit {i}: [{hit['doc_title']}] § {hit['section']} (Score: {hit['score']})")
        print(f"  Snippet: {hit['snippet'][:120]}...\n")

    print("=== 3. Fault Taxonomy Lookup ===")
    f = await kb.get_kb_fault("GAS_LOCK")
    print("Fault:", f["preferred_name"])
    print("Category:", f["category"])
    print("Symptoms:", f["symptoms"])
    print("Contributing Factors:", f["contributing_factors"])

    print("\n=== 4. Causal Graph Recursive Trace ===")
    g = await kb.trace_kb_graph(["Low Intake Pressure (<150 psi)", "High Motor Temperature (>130°C)"])
    print("Causal Trace Paths:", len(g["paths"]))
    print("Root Causes Identified:", g["root_causes"])

if __name__ == "__main__":
    asyncio.run(main())
