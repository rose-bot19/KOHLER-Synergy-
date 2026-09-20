from document_manager import (
    classify_document,
    ingest_document,
)


file_path = "inbox/updated_smart_toilet_warranty.txt"


print("\n--- CLASSIFICATION ---")

result = classify_document(file_path)

print(result)


print("\n--- SIMULATING USER CONFIRMATION ---")

result = ingest_document(
    file_path,
    category="policies",
)

print(result)