import json
from concurrent.futures import ThreadPoolExecutor, as_completed


def _load_prompt(file_path):
    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        return file.read()


def run_worker(
    client,
    worker_name,
    task,
    evidence,
):
    """Run one specialized worker."""

    system_prompt = _load_prompt(
        "prompts/worker.txt"
    )

    worker_prompt = f"""
WORKER SPECIALIZATION:
{worker_name}

TASK:
{task}

EVIDENCE:
{evidence}
"""

    interaction = client.interactions.create(

        model="gemini-3.6-flash",

        input=worker_prompt,

        system_instruction=system_prompt,

        response_format={
            "type": "text",
            "mime_type": "application/json",

            "schema": {
                "type": "object",

                "properties": {

                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                    },

                    "supported_claims": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                    },

                    "information_missing": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                    },
                },

                "required": [
                    "findings",
                    "supported_claims",
                    "information_missing",
                ],
            },
        },
    )

    return json.loads(
        interaction.output_text
    )


def run_workers(
    client,
    tasks,
):
    """Run independent workers concurrently."""

    results = []

    with ThreadPoolExecutor(
        max_workers=min(len(tasks), 3)
    ) as executor:

        future_map = {}

        for task in tasks:

            future = executor.submit(
                run_worker,
                client,
                task["worker"],
                task["task"],
                task["evidence"],
            )

            future_map[future] = task

        for future in as_completed(
            future_map
        ):

            task = future_map[future]

            try:

                result = future.result()

                results.append({
                    "worker":
                        task["worker"],

                    "task":
                        task["task"],

                    "result":
                        result,
                })

            except Exception as error:

                results.append({
                    "worker":
                        task["worker"],

                    "task":
                        task["task"],

                    "result": {
                        "findings": [],
                        "supported_claims": [],
                        "information_missing": [
                            f"Worker failed: {error}"
                        ],
                    },
                })

    return results