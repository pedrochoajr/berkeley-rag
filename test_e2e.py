from pipeline.rag_pipeline import RAGPipeline

pipeline = RAGPipeline()

# ── Semantic queries — pipeline handles these well ─────────────────────────────

semantic_queries = [
    # Course discovery
    "I want to learn machine learning, what should I take?",
    "Find me an upper division CS course about algorithms",
    "What math courses cover linear algebra?",
    "I'm interested in probability and statistics, what courses exist?",

    # Department filtered
    "What are good entry level EECS courses?",
    "Find me a 4 unit upper division COMPSCI course",

    # Topic based
    "What courses cover neural networks and deep learning?",
    "I want to understand how computers work at a low level",
    "Find me courses about data structures and algorithms",
    "What courses involve Python programming?",
]

# ── Prerequisite queries — will work once LangGraph agent is built ─────────────

prerequisite_queries = [
    "What are the prerequisites for CS 189?",
    "What can I take after completing MATH 54?",
    "Can I take CS 189 if I've completed MATH 53?",
    "What is the full prerequisite chain to get to CS 189?",
]

# ── Guardrail queries — should be blocked once guardrails are built ────────────

off_topic_queries = [
    "What is the weather today?",
    "Help me write my essay",
    "Who is the president of the United States?",
]

# ── Run tests ──────────────────────────────────────────────────────────────────

def run_queries(queries: list[str], label: str):
    print(f"\n{'='*60}")
    print(f" {label}")
    print(f"{'='*60}")

    passed = 0
    failed = 0

    for query in queries:
        print(f"\nQ: {query}")
        print("-" * 50)

        response = pipeline.query(query)
        answer = response["answer"]
        sources = response["sources"]

        print(f"A: {answer}")
        print(f"Sources: {sources}")

        # Basic quality checks
        has_answer = len(answer) > 20
        has_sources = len(sources) > 0
        not_fallback = "don't have enough information" not in answer.lower()

        if has_answer and has_sources and not_fallback:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            if not has_answer:
                print("   → Answer too short")
            if not has_sources:
                print("   → No sources returned")
            if not not_fallback:
                print("   → Returned fallback response")
            failed += 1

    print(f"\n{'─'*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(queries)}")
    return passed, failed


def run_prerequisite_preview(queries: list[str]):
    print(f"\n{'='*60}")
    print(f" PREREQUISITE QUERIES (expected to fail — needs agent)")
    print(f"{'='*60}")

    for query in queries:
        print(f"\nQ: {query}")
        print("-" * 50)
        response = pipeline.query(query)
        print(f"A: {response['answer'][:150]}...")
        print(f"Sources: {response['sources']}")
        print("⚠️  Will be fixed by LangGraph agent → Neo4j traversal")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    total_passed = 0
    total_failed = 0

    # Run semantic queries
    passed, failed = run_queries(semantic_queries, "SEMANTIC QUERIES")
    total_passed += passed
    total_failed += failed

    # Show prerequisite query limitation
    run_prerequisite_preview(prerequisite_queries)

    # Summary
    print(f"\n{'='*60}")
    print(f" FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Semantic queries:     {total_passed}/{len(semantic_queries)} passed")
    #print(f"Prerequisite queries: 0/{len(prerequisite_queries)} (needs agent)")
    #print(f"Off-topic queries:    0/{len(off_topic_queries)} (needs guardrails)")