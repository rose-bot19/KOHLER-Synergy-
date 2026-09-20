import json
import os
from types import SimpleNamespace

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


OPENROUTER_MODEL = "openrouter/free"


class OpenRouterFallback:

    def __init__(self):
        api_key = os.getenv(
            "OPENROUTER_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is missing "
                "from the .env file."
            )

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        self.messages = []

    # -----------------------------------------------------
    # START A NEW FALLBACK CONVERSATION
    # -----------------------------------------------------

    def start(
        self,
        system_prompt,
        user_message,
    ):

        self.messages = [

            {
                "role": "system",
                "content": system_prompt,
            },

            {
                "role": "user",
                "content": user_message,
            },
        ]

    # -----------------------------------------------------
    # SEED FALLBACK FROM A GEMINI TOOL CALL
    # -----------------------------------------------------

    def seed_from_gemini(
        self,
        system_prompt,
        user_message,
        function_calls,
        function_results,
    ):

        self.messages = [

            {
                "role": "system",
                "content": system_prompt,
            },

            {
                "role": "user",
                "content": user_message,
            },
        ]

        # Reconstruct the assistant's tool request.

        if function_calls:

            tool_calls = []

            for step in function_calls:

                arguments = step.arguments

                if not isinstance(
                    arguments,
                    str,
                ):
                    arguments = json.dumps(
                        arguments
                    )

                tool_calls.append(
                    {
                        "id": step.id,
                        "type": "function",
                        "function": {
                            "name": step.name,
                            "arguments": arguments,
                        },
                    }
                )

            self.messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls,
                }
            )

        self.add_tool_results(
            function_results
        )

    # -----------------------------------------------------
    # SEND TOOL RESULTS
    # -----------------------------------------------------

    def add_tool_results(
        self,
        function_results,
    ):

        for result in function_results:

            call_id = result.get(
                "call_id"
            )

            result_data = result.get(
                "result",
                [],
            )

            text_parts = []

            for item in result_data:

                if isinstance(
                    item,
                    dict,
                ):
                    text_parts.append(
                        str(
                            item.get(
                                "text",
                                "",
                            )
                        )
                    )

                else:
                    text_parts.append(
                        str(item)
                    )

            content = "\n".join(
                text_parts
            )

            self.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": content,
                }
            )

    # -----------------------------------------------------
    # CALL OPENROUTER
    # -----------------------------------------------------

    def send(
        self,
        tools,
    ):

        response = (
            self.client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=self.messages,
                tools=tools,
            )
        )

        message = response.choices[0].message

        # Save assistant response into the
        # OpenRouter conversation.

        assistant_message = {
            "role": "assistant",
            "content": (
                message.content
                or None
            ),
        }

        if message.tool_calls:

            assistant_message[
                "tool_calls"
            ] = []

            for call in message.tool_calls:

                assistant_message[
                    "tool_calls"
                ].append(
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": (
                                call.function.name
                            ),
                            "arguments": (
                                call.function.arguments
                            ),
                        },
                    }
                )

        self.messages.append(
            assistant_message
        )

        # Convert OpenRouter's response into
        # the same simple shape your existing
        # _process_interaction() expects.

        steps = []

        if message.tool_calls:

            for call in message.tool_calls:

                try:

                    arguments = json.loads(
                        call.function.arguments
                    )

                except json.JSONDecodeError:

                    arguments = {}

                steps.append(
                    SimpleNamespace(
                        type="function_call",
                        id=call.id,
                        name=call.function.name,
                        arguments=arguments,
                    )
                )

        return SimpleNamespace(
            id=f"openrouter-{response.id}",
            steps=steps,
            output_text=(
                message.content
                or ""
            ),
        )

    @property
    def client_for_verification(self):
        return self.client