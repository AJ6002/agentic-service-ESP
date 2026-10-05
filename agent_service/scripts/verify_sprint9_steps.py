import json
import urllib.request
import sys

def post_kb_search(query: str, top_k: int = 3):
    url = "http://127.0.0.1:8091/kb/search"
    payload = {"query": query, "top_k": top_k}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    print("=" * 80)
    print("STEP 4: SEMANTIC SEARCH VERIFICATION")
    print("=" * 80)

    # Query 1
    q1 = "what does the subsystem equalizer show"
    res1 = post_kb_search(q1, top_k=3)
    hits1 = res1.get("hits", [])
    print(f"\n[Query 1] '{q1}' (top_k=3):")
    for i, h in enumerate(hits1, 1):
        print(f"  [{i}] chunk_id: {h.get('chunk_id')}")
        print(f"      doc_title: {h.get('doc_title')}")
        print(f"      score: {h.get('score'):.4f}")
        print(f"      snippet: {h.get('snippet', '')[:100]}...")

    top_id_1 = hits1[0].get("chunk_id", "") if hits1 else ""
    assert "component.subsystem-equalizer" in top_id_1, f"Expected component.subsystem-equalizer, got {top_id_1}"
    print("  -> PASS: Top hit is component.subsystem-equalizer")

    # Query 2
    q2 = "working status dashboard"
    res2 = post_kb_search(q2, top_k=3)
    hits2 = res2.get("hits", [])
    print(f"\n[Query 2] '{q2}' (top_k=3):")
    for i, h in enumerate(hits2, 1):
        print(f"  [{i}] chunk_id: {h.get('chunk_id')}")
        print(f"      doc_title: {h.get('doc_title')}")
        print(f"      score: {h.get('score'):.4f}")

    # Query 3
    q3 = "what does PIP mean"
    res3 = post_kb_search(q3, top_k=3)
    hits3 = res3.get("hits", [])
    print(f"\n[Query 3] '{q3}' (top_k=3):")
    for i, h in enumerate(hits3, 1):
        print(f"  [{i}] chunk_id: {h.get('chunk_id')}")
        print(f"      doc_title: {h.get('doc_title')}")
        print(f"      score: {h.get('score'):.4f}")

    print("\n" + "=" * 80)
    print("STEP 5: DOMAIN ISOLATION VERIFICATION")
    print("=" * 80)

    q5 = "gas lock in ESP"
    res5 = post_kb_search(q5, top_k=5)
    hits5 = res5.get("hits", [])
    print(f"\n[Query 5] '{q5}' (top_k=5):")
    ui_map_hits = []
    for i, h in enumerate(hits5, 1):
        cid = h.get("chunk_id", "")
        is_ui = "ui_map" in cid
        if is_ui:
            ui_map_hits.append(cid)
        print(f"  [{i}] chunk_id: {cid} (ui_map={is_ui})")
        print(f"      doc_title: {h.get('doc_title')}")
        print(f"      score: {h.get('score'):.4f}")

    assert len(ui_map_hits) == 0, f"Expected 0 ui_map entries in top 5, got: {ui_map_hits}"
    print(f"  -> PASS: Zero ui_map entries in top 5 (ui_map_hits={len(ui_map_hits)})")

if __name__ == "__main__":
    main()
