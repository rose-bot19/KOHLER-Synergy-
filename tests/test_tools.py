from tools import (
    search_knowledge_base,
    check_warranty,
    create_support_ticket,
    get_ticket,
)


print("\n--- WARRANTY TEST ---")
print(check_warranty("Kohler smart toilet"))


print("\n--- KNOWLEDGE TEST ---")
print(search_knowledge_base("smart toilet leaking"))


print("\n--- CREATE TICKET TEST ---")
result = create_support_ticket(
    "Eden",
    "Kohler smart toilet",
    "Toilet is leaking"
)

print(result)


print("\n--- LOOK UP TICKET TEST ---")
print(get_ticket("KT-1001"))