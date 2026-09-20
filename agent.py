import os

from dotenv import load_dotenv
from google import genai
from prompt_loader import load_prompt_bundle

load_dotenv()


MODEL = "gemini-3.6-flash"


def load_system_prompt():
    """Load Kohler Synergy's system instructions."""

    return load_prompt_bundle()


def create_client():
    """Create the Gemini API client."""

    api_key = os.getenv("GEMINI_API_KEY")

    return genai.Client(api_key=api_key)


TOOL_DECLARATIONS = [

    {
        "type": "function",
        "name": "search_knowledge_base",
        "description": (
            "Search the KOHLER enterprise knowledge base "
            "for relevant company information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The information to search for."
                    ),
                }
            },
            "required": ["query"],
        },
    },

    {
        "type": "function",
        "name": "check_warranty",
        "description": (
            "Check warranty information for a KOHLER product."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "string",
                    "description": (
                        "The KOHLER product to check."
                    ),
                }
            },
            "required": ["product"],
        },
    },

    {
        "type": "function",
        "name": "create_support_ticket",
        "description": (
            "Create a support ticket for a customer's issue."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer": {
                    "type": "string"
                },
                "product": {
                    "type": "string"
                },
                "issue": {
                    "type": "string"
                },
            },
            "required": [
                "customer",
                "product",
                "issue",
            ],
        },
    },

    {
        "type": "function",
        "name": "get_ticket",
        "description": (
            "Look up an existing KOHLER support ticket."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": (
                        "The support ticket ID, such as KT-1001."
                    ),
                }
            },
            "required": ["ticket_id"],
        },
    },

    {
        "type": "function",
        "name": "delegate_complex_task",
        "description": (
            "Delegate a complex multi-domain task to "
            "specialized internal workers when appropriate."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": (
                        "The complex task to delegate."
                    ),
                }
            },
            "required": ["task"],
        },
    },

    {
        "type": "function",
        "name": "save_memory",
        "description": (
            "Store a useful durable fact or event from the "
            "conversation that may help in future interactions. "
            "Only use this when the information is genuinely "
            "useful beyond the current turn."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": (
                        "The useful fact or event to remember."
                    ),
                },
                "tags": {
                    "type": "string",
                    "description": (
                        "Optional comma-separated memory tags."
                    ),
                },
            },
            "required": [
                "summary"
            ],
        },
    },

    {
        "type": "function",
        "name": "recall_memory",
        "description": (
            "Search Synergy's previous episodic memories "
            "for information relevant to the current request."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Information to search for in memory."
                    ),
                },
            },
            "required": [
                "query"
            ],
        },
    },
    {
    "type": "function",
    "name": "send_email",
    "description": (
        "Send an email to a specified recipient. "
        "This is a high-risk action and requires human approval."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "recipient": {
                "type": "string"
            },
            "subject": {
                "type": "string"
            },
            "body": {
                "type": "string"
            },
        },
        "required": [
            "recipient",
            "subject",
            "body",
        ],
    },
},

{
    "type": "function",
    "name": "update_customer_record",
    "description": (
        "Update an existing enterprise customer record. "
        "This is a high-risk action and requires human approval."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "customer_name": {
                "type": "string"
            },
            "fields": {
                "type": "object",
                "additionalProperties": True,
            },
        },
        "required": [
            "customer_name",
            "fields",
        ],
    },
},

{
    "type": "function",
    "name": "delete_record",
    "description": (
        "Delete an enterprise record. "
        "This is a high-risk action and requires human approval."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "record_type": {
                "type": "string"
            },
            "record_id": {
                "type": "string"
            },
        },
        "required": [
            "record_type",
            "record_id",
        ],
    },
},

{
    "type": "function",
    "name": "create_maintenance_dispatch",
    "description": (
        "Create a facilities or maintenance dispatch. "
        "This is a high-risk action and requires human approval."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "customer": {
                "type": "string"
            },
            "location": {
                "type": "string"
            },
            "issue": {
                "type": "string"
            },
            "priority": {
                "type": "string"
            },
        },
        "required": [
            "customer",
            "location",
            "issue",
        ],
    },
},

{
    "type": "function",
    "name": "store_document",
    "description": (
        "Store an approved company document "
        "in the selected knowledge-base category."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string"
            },
            "category": {
                "type": "string"
            },
        },
        "required": [
            "file_path",
            "category",
        ],
    },
},
]
