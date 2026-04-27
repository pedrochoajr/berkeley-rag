from pipeline.rag_pipeline import RAGPipeline

pipeline = RAGPipeline()

questions = [
    "What are the prerequisites for CS 189 at UC Berkeley?"
]

for question in questions:
    print(f"\nQ: {question}")
    print("-" * 50)
    response = pipeline.query(question)
    print(f"A: {response['answer']}")
    print(f"Sources: {response['sources']}")