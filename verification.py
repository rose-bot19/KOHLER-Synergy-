import re
import json


def _has_concrete_facts(text):

    patterns = [
        r"\bKT-\d+\b",
        r"\b\d{4}\b",
        r"\b\d+(?:\.\d+)?%\b",
        r"\b\d+(?:\.\d+)?\s*(?:year|years|month|months|day|days)\b",
        r"₹\s*[\d,]+",
    ]

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def needs_ai_verification(
    answer,
    evidence,
):
    """
    Cheap trigger only.

    We use this to decide whether an expensive
    semantic verification call is worthwhile.

    It does NOT decide whether the answer is correct.
    """

    if not evidence:
        return False

    return _has_concrete_facts(
        answer
    )


def verify_response_with_ai(
    client,
    answer,
    evidence,
):
    """
    Use Gemini to semantically verify the response
    against supplied enterprise evidence.
    """

    prompt = f"""
You are the verification component of KOHLER Synergy.

Review the proposed response against the supplied evidence.

Determine whether the response contains claims that are unsupported
or contradicted by the evidence.

Do not use outside knowledge.

PROPOSED RESPONSE:
{answer}

EVIDENCE:
{chr(10).join(evidence)}
"""

    interaction = client.interactions.create(

        model="gemini-3.6-flash",

        input=prompt,

        response_format={
            "type": "text",

            "mime_type":
                "application/json",

            "schema": {

                "type": "object",

                "properties": {

                    "status": {
                        "type": "string",
                        "enum": [
                            "verified",
                            "review",
                        ],
                    },

                    "issues": {
                        "type": "array",

                        "items": {
                            "type": "string"
                        },
                    },
                },

                "required": [
                    "status",
                    "issues",
                ],
            },
        },
    )


    return json.loads(
        interaction.output_text
    )