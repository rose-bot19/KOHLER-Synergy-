import json
import os
from connectors import SupportConnector
from audit import log_event
from manager import run_complex_task

from memory import (
    remember_episode,
    search_memory,
)

from enterprise_actions import (
    send_email,
    update_customer_record,
    delete_record,
    create_maintenance_dispatch,
    store_document,
)

support_connector = SupportConnector()


#KNOWLEDGE BASE

def search_knowledge_base(query: str) -> str:
    """Search the Kohler knowledge base for relevant information."""

    results = []

    documents = [
        ("Warranty Policy", "knowledge/warranty_policy.txt"),
        ("Customer Support Guidelines", "knowledge/customer_support.txt"),
    ]

    query_words = query.lower().split()

    for document_name, file_path in documents:

        with open(file_path, "r", encoding="utf-8") as file:
            document_text = file.read()

        matches = 0

        for word in query_words:
            if word in document_text.lower():
                matches += 1

        if matches > 0:
            results.append(
                f"--- {document_name} ---\n{document_text}"
            )

    if results:
        return "\n\n".join(results)

    return "No relevant information was found."


#WARRANTY TOOL

def check_warranty(product: str) -> str:
    """Check the warranty status of a Kohler product."""

    warranty_database = {
        "smart toilet": "Under warranty until December 2027.",
        "faucet": "Warranty ended in June 2026.",
        "thermostatic shower": "Under warranty until March 2028.",
    }

    product = product.lower()

    for item in warranty_database:
        if item in product:
            return warranty_database[item]

    return "Warranty information not found."


#SUPPORT TICKET TOOL

def create_support_ticket(
    customer: str,
    product: str,
    issue: str
) -> str:
    """Create a support ticket through the support connector."""

    ticket = support_connector.create_ticket(
        customer,
        product,
        issue
    )

    log_event(
        "ACTION_COMPLETED",
        action="create_support_ticket",
        ticket_id=ticket["ticket_id"],
        customer=customer,
        product=product,
    )

    return (
        f"Support ticket {ticket['ticket_id']} created successfully. "
        f"Customer: {ticket['customer']}. "
        f"Product: {ticket['product']}. "
        f"Issue: {ticket['issue']}. "
        f"Status: {ticket['status']}."
    )


def get_ticket(ticket_id: str) -> str:
    """Retrieve a support ticket through the support connector."""

    ticket = support_connector.get_ticket(ticket_id)

    if ticket is None:
        return f"Ticket {ticket_id} was not found."

    return (
        f"Ticket {ticket['ticket_id']}:\n"
        f"Customer: {ticket['customer']}\n"
        f"Product: {ticket['product']}\n"
        f"Issue: {ticket['issue']}\n"
        f"Status: {ticket['status']}"
    )




#delegate complex tasks to the manager
def delegate_complex_task(task: str) -> str:
    """Delegate a complex task to Synergy's Manager and Workers."""

    return run_complex_task(task)


#memory management tools
def save_memory(
    summary: str,
    tags: str = ""
) -> str:

    tag_list = [
        tag.strip()
        for tag in tags.split(",")
        if tag.strip()
    ]

    result = remember_episode(
        summary,
        tag_list,
    )

    return (
        f"Memory saved: {result['summary']}"
    )


def recall_memory(
    query: str
) -> str:

    memories = search_memory(
        query
    )

    if not memories:
        return "No relevant previous memory found."

    return "\n\n".join(
        memory["summary"]
        for memory in memories
    )


TOOL_FUNCTIONS = {
    "search_knowledge_base": search_knowledge_base,
    "check_warranty": check_warranty,
    "create_support_ticket": create_support_ticket,
    "get_ticket": get_ticket,
    "delegate_complex_task": delegate_complex_task,
    "save_memory": save_memory,
    "recall_memory": recall_memory,

    "send_email": send_email,
    "update_customer_record": update_customer_record,
    "delete_record": delete_record,
    "create_maintenance_dispatch": create_maintenance_dispatch,
    "store_document": store_document,
}
