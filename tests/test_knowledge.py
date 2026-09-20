from knowledge_base import search_knowledge


print("\n--- SEMANTIC SEARCH TEST ---")

results = search_knowledge(
    "What should a customer do if their smart toilet has a leak?"
)

for document, metadata in zip(
    results["documents"][0],
    results["metadatas"][0]
):
    print("\nSOURCE:", metadata["source"])
    print("CONTENT:")
    print(document)