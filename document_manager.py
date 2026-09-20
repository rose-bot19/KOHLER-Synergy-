import json
import os
import shutil

from dotenv import load_dotenv
from google import genai

from knowledge_base import index_document
from audit import log_event


load_dotenv()


KNOWLEDGE_ROOT = "knowledge"
INBOX = "inbox"

REGISTRY_FILE = "data/document_registry.json"


CATEGORIES = [
    "policies",
    "products",
    "support",
    "projects",
    "facilities",
    "finance",
    "compliance",
]


#REGISTRY

def _load_registry():

    if not os.path.exists(
        REGISTRY_FILE
    ):
        return []

    with open(
        REGISTRY_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def _save_registry(
    registry
):

    os.makedirs(
        "data",
        exist_ok=True,
    )

    with open(
        REGISTRY_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            registry,
            file,
            indent=4,
        )


#DOCUMENT TEXT

def extract_document_text(
    file_path
):

    extension = os.path.splitext(
        file_path
    )[1].lower()


    if extension in {
        ".txt",
        ".md",
    }:

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            return file.read()


    if extension == ".pdf":

        from pypdf import PdfReader

        reader = PdfReader(
            file_path
        )

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n\n".join(
            pages
        )


    raise ValueError(
        f"Unsupported file type: {extension}"
    )


#AI DOCUMENT CLASSIFICATION

def classify_document(
    file_path
):
    """
    Ask Gemini to understand what a document actually is.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    client = genai.Client(
        api_key=api_key
    )


    text = extract_document_text(
        file_path
    )


    text_sample = text[:15000]


    prompt = f"""
You are the document intelligence component of KOHLER Synergy.

Analyze this enterprise document based on its actual meaning and purpose.

Choose exactly one category:

{", ".join(CATEGORIES)}

Also identify:

- document_key: a stable name for the document or policy family
- version: version number if stated, otherwise "unknown"
- effective_date: date if stated, otherwise "unknown"
- short_reason: one short sentence explaining the classification
- needs_confirmation: true when classification or document identity
  is uncertain

Do not classify based only on the filename.

DOCUMENT:
{text_sample}
"""


    interaction = client.interactions.create(

        model="gemini-3.6-flash",

        input=prompt,

        response_format={

            "type": "text",

            "mime_type": "application/json",

            "schema": {

                "type": "object",

                "properties": {

                    "category": {
                        "type": "string",
                        "enum": CATEGORIES,
                    },

                    "document_key": {
                        "type": "string",
                    },

                    "version": {
                        "type": "string",
                    },

                    "effective_date": {
                        "type": "string",
                    },

                    "short_reason": {
                        "type": "string",
                    },

                    "needs_confirmation": {
                        "type": "boolean",
                    },
                },

                "required": [
                    "category",
                    "document_key",
                    "version",
                    "effective_date",
                    "short_reason",
                    "needs_confirmation",
                ],
            },
        },
    )


    result = json.loads(
        interaction.output_text
    )


    log_event(
        "DOCUMENT_CLASSIFIED",
        file=file_path,
        category=result["category"],
        document_key=result["document_key"],
        version=result["version"],
    )


    return result


#STORE DOCUMENT

def ingest_document(
    file_path,
    classification,
):
    """
    Store an approved document and update the knowledge base.
    """

    category = classification[
        "category"
    ]

    document_key = classification[
        "document_key"
    ]

    version = classification[
        "version"
    ]

    effective_date = classification[
        "effective_date"
    ]


    if category not in CATEGORIES:

        return {
            "status": "failed",
            "message": (
                f"Unknown category: {category}"
            ),
        }


    destination_folder = os.path.join(
        KNOWLEDGE_ROOT,
        category,
    )

    os.makedirs(
        destination_folder,
        exist_ok=True,
    )


    filename = os.path.basename(
        file_path
    )

    destination = os.path.join(
        destination_folder,
        filename,
    )


    # -----------------------------------------------------
    # VERSION MANAGEMENT
    # -----------------------------------------------------

    registry = _load_registry()


    updated_registry = []


    for document in registry:

        if (
            document.get("document_key")
            == document_key
        ):

            document["status"] = "superseded"


        updated_registry.append(
            document
        )


    #MOVE DOCUMENT

    if os.path.abspath(
        file_path
    ) != os.path.abspath(
        destination
    ):

        shutil.move(
            file_path,
            destination,
        )


    metadata = {

        "category":
            category,

        "document_key":
            document_key,

        "version":
            version,

        "effective_date":
            effective_date,

        "status":
            "active",
    }


    #INDEX NEW DOCUMENT

    index_document(
        destination,
        metadata,
    )


    #SAVE REGISTRY

    updated_registry.append({

        "document_key":
            document_key,

        "version":
            version,

        "effective_date":
            effective_date,

        "category":
            category,

        "path":
            destination,

        "status":
            "active",
    })


    _save_registry(
        updated_registry
    )


    log_event(
        "DOCUMENT_INGESTED",
        document_key=document_key,
        version=version,
        category=category,
        path=destination,
    )


    return {

        "status":
            "success",

        "message":
            "Document added to the knowledge base.",

        "document":
            document_key,

        "version":
            version,

        "category":
            category,

        "path":
            destination,
    }
