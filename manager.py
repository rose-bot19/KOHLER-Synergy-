import json

from google import genai

from workers import run_workers


WORKER_TYPES = [
    "knowledge_worker",
    "warranty_worker",
    "project_worker",
]


def _load_prompt(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        return file.read()


def _collect_evidence(
    worker_name,
    task,
):
    """
    Collect only the evidence relevant to
    the worker's assignment.
    """

    from tools import (
        search_knowledge_base,
        check_warranty,
    )

    if worker_name == "knowledge_worker":

        return search_knowledge_base(
            task
        )


    if worker_name == "warranty_worker":

        return check_warranty(
            task
        )


    if worker_name == "project_worker":

        return search_knowledge_base(
            task
        )


    return "No evidence source is available."


def plan_complex_task(
    client,
    user_request,
):
    """Ask the Manager to decompose a complex request."""

    manager_prompt = _load_prompt(
        "prompts/manager.txt"
    )

    interaction = client.interactions.create(

        model="gemini-3.6-flash",

        input=user_request,

        system_instruction=manager_prompt,

        response_format={
            "type": "text",
            "mime_type": "application/json",

            "schema": {
                "type": "object",

                "properties": {

                    "tasks": {
                        "type": "array",

                        "items": {

                            "type": "object",

                            "properties": {

                                "worker": {
                                    "type": "string",
                                    "enum": WORKER_TYPES,
                                },

                                "task": {
                                    "type": "string",
                                },
                            },

                            "required": [
                                "worker",
                                "task",
                            ],
                        },
                    },
                },

                "required": [
                    "tasks",
                ],
            },
        },
    )

    return json.loads(
        interaction.output_text
    )


def run_complex_task(
    user_request,
):
    """
    Full Manager → Workers → Synthesizer workflow.
    """

    client = genai.Client()


    #MANAGER

    plan = plan_complex_task(
        client,
        user_request,
    )


    tasks = plan.get(
        "tasks",
        []
    )[:3]


    #COLLECT RELEVANT EVIDENCE

    prepared_tasks = []

    for task in tasks:

        worker = task["worker"]

        task_description = task["task"]

        evidence = _collect_evidence(
            worker,
            task_description,
        )

        prepared_tasks.append({

            "worker":
                worker,

            "task":
                task_description,

            "evidence":
                evidence,
        })


    #PARALLEL WORKERS

    worker_results = run_workers(
        client,
        prepared_tasks,
    )


    #SYNTHESIS

    synthesis_prompt = _load_prompt(
        "prompts/synthesizer.txt"
    )

    synthesis_input = f"""
USER REQUEST:
{user_request}

WORKER FINDINGS:
{json.dumps(worker_results, indent=2)}
"""


    interaction = client.interactions.create(

        model="gemini-3.6-flash",

        input=synthesis_input,

        system_instruction=synthesis_prompt,
    )


    return interaction.output_text
