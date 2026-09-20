
import os

PROMPT_ROOT = "prompts"


def load_prompt(filename):
    """Load one prompt file from the prompts folder."""
    path = os.path.join(
        PROMPT_ROOT,
        filename,
    )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return file.read()


def load_prompt_bundle():
    """
    Load the modular Synergy prompts and combine them
    into one system-instruction package.
    """

    prompt_files = [
        "system_prompt.txt",
        "intent_router.txt",
        "response_strategy.txt",
        "manager.txt",
        "worker.txt",
        "synthesizer.txt",
        "verification.txt",
        "document_classifier.txt",
        "memory_extraction.txt",
        "response_formatter.txt",
    ]

    sections = []

    for filename in prompt_files:
        try:
            content = load_prompt(filename)

            sections.append(
                f"""
===== {filename} =====

{content}
"""
            )

        except FileNotFoundError:
            # If one optional prompt is missing,
            # continue loading the remaining prompts.
            continue

    return "\n".join(sections)

