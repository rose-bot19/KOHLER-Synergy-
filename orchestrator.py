
import json
import os
from types import SimpleNamespace

from openai import OpenAI

from agent import (
    MODEL,
    TOOL_DECLARATIONS,
    create_client,
    load_system_prompt,
)

from tools import TOOL_FUNCTIONS

from action_policy import assess_action

from audit import log_event

from verification import (
    needs_ai_verification,
    verify_response_with_ai,
)


OPENROUTER_MODEL = "openrouter/free"

MAX_AGENT_STEPS = 8


class SynergyOrchestrator:

    def __init__(self):

        # -------------------------------------------------
        # PRIMARY PROVIDER
        # -------------------------------------------------

        self.client = create_client()

        self.provider = "gemini"

        self.system_prompt = (
            load_system_prompt()
        )

        self.previous_interaction_id = None

        # -------------------------------------------------
        # OPENROUTER FALLBACK
        # -------------------------------------------------

        self.openrouter_client = None

        self.openrouter_messages = []

        # -------------------------------------------------
        # PROVIDER-INDEPENDENT HISTORY
        # -------------------------------------------------

        self.conversation_history = []

        # -------------------------------------------------
        # AGENT STATE
        # -------------------------------------------------

        self.pending_action = None

        self.last_evidence = []

        self.last_function_calls = []

        self.current_user_message = ""

    # =====================================================
    # RESTORE CONVERSATION HISTORY
    # =====================================================

    def set_history(
        self,
        history,
    ):
        """
        Restore the user/assistant conversation when
        a saved conversation is loaded.
        """

        restored = []

        for message in history:

            role = message.get(
                "role"
            )

            content = message.get(
                "content"
            )

            if role not in {
                "user",
                "assistant",
            }:
                continue

            if content is None:
                continue

            restored.append(
                {
                    "role": role,
                    "content": str(content),
                }
            )

        self.conversation_history = restored

        if self.provider == "openrouter":

            self._initialize_openrouter_history()

    # =====================================================
    # CREATE OPENROUTER CLIENT
    # =====================================================

    def _create_openrouter_client(self):

        if self.openrouter_client is not None:
            return self.openrouter_client

        api_key = os.getenv(
            "OPENROUTER_API_KEY"
        )

        if not api_key:

            raise RuntimeError(
                "OPENROUTER_API_KEY is missing "
                "from the .env file."
            )

        self.openrouter_client = OpenAI(
            base_url=(
                "https://openrouter.ai/api/v1"
            ),
            api_key=api_key,
        )

        return self.openrouter_client

    # =====================================================
    # CONVERT TOOL DECLARATIONS
    # =====================================================

    def _get_openrouter_tools(self):

        converted = []

        for declaration in TOOL_DECLARATIONS:

            # Already OpenAI-compatible.

            if "function" in declaration:

                converted.append(
                    declaration
                )

                continue

            # Gemini-style fallback.

            converted.append(
                {
                    "type": "function",
                    "function": {
                        "name": declaration.get(
                            "name"
                        ),
                        "description": declaration.get(
                            "description",
                            "",
                        ),
                        "parameters": declaration.get(
                            "parameters",
                            {
                                "type": "object",
                                "properties": {},
                            },
                        ),
                    },
                }
            )

        return converted

    # =====================================================
    # INITIALIZE OPENROUTER HISTORY
    # =====================================================

    def _initialize_openrouter_history(self):

        self._create_openrouter_client()

        self.openrouter_messages = [

            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

        for message in self.conversation_history:

            role = message.get(
                "role"
            )

            content = message.get(
                "content"
            )

            if role not in {
                "user",
                "assistant",
            }:
                continue

            self.openrouter_messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

    # =====================================================
    # ACTIVATE FALLBACK
    # =====================================================

    def _activate_openrouter_fallback(
        self,
        reason,
    ):

        if self.provider == "openrouter":
            return

        log_event(
            "MODEL_FALLBACK",
            from_provider="gemini",
            to_provider="openrouter",
            reason=str(reason),
        )

        self.provider = "openrouter"

        self._initialize_openrouter_history()

        log_event(
            "OPENROUTER_FALLBACK_ACTIVE"
        )

    # =====================================================
    # GEMINI INTERACTION
    # =====================================================

    def _create_gemini_interaction(
        self,
        input_data,
        previous_interaction_id=None,
    ):
        """
        Existing Gemini Interactions API path.
        """

        return self.client.interactions.create(

            model=MODEL,

            input=input_data,

            previous_interaction_id=(
                previous_interaction_id
            ),

            system_instruction=(
                load_system_prompt()
            ),

            tools=TOOL_DECLARATIONS,
        )

    # =====================================================
    # OPENROUTER INTERACTION
    # =====================================================

    def _create_openrouter_interaction(
        self,
        input_data,
    ):
        """
        OpenRouter uses the OpenAI-compatible chat
        completions interface.
        """

        if not self.openrouter_messages:

            self._initialize_openrouter_history()

        # -------------------------------------------------
        # Add tool results
        # -------------------------------------------------

        if isinstance(
            input_data,
            list,
        ):

            for function_result in input_data:

                call_id = function_result.get(
                    "call_id"
                )

                result_items = (
                    function_result.get(
                        "result",
                        [],
                    )
                )

                text_parts = []

                for item in result_items:

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

                self.openrouter_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": content,
                    }
                )

        client = (
            self._create_openrouter_client()
        )

        response = (
            client.chat.completions.create(

                model=OPENROUTER_MODEL,

                messages=(
                    self.openrouter_messages
                ),

                tools=(
                    self._get_openrouter_tools()
                ),
            )
        )

        message = (
            response.choices[0].message
        )

        # -------------------------------------------------
        # Convert response into the same simple structure
        # expected by _process_interaction()
        # -------------------------------------------------

        steps = []

        openrouter_tool_calls = []

        if message.tool_calls:

            for call in message.tool_calls:

                raw_arguments = (
                    call.function.arguments
                    or "{}"
                )

                try:

                    arguments = json.loads(
                        raw_arguments
                    )

                except json.JSONDecodeError:

                    arguments = {}

                steps.append(
                    SimpleNamespace(

                        type="function_call",

                        id=call.id,

                        name=(
                            call.function.name
                        ),

                        arguments=arguments,
                    )
                )

                openrouter_tool_calls.append(
                    {
                        "id": call.id,

                        "type": "function",

                        "function": {

                            "name":
                                call.function.name,

                            "arguments":
                                raw_arguments,
                        },
                    }
                )

        # -------------------------------------------------
        # Store assistant response
        # -------------------------------------------------

        assistant_message = {

            "role": "assistant",

            "content": (
                message.content
                or None
            ),
        }

        if openrouter_tool_calls:

            assistant_message[
                "tool_calls"
            ] = openrouter_tool_calls

        self.openrouter_messages.append(
            assistant_message
        )

        return SimpleNamespace(

            id=(
                f"openrouter-"
                f"{response.id}"
            ),

            steps=steps,

            output_text=(
                message.content
                or ""
            ),
        )

    # =====================================================
    # UNIFIED INTERACTION CREATOR
    # =====================================================

    def _create_interaction(
        self,
        input_data,
        previous_interaction_id=None,
    ):
        """
        Gemini is the primary model.

        If Gemini reports quota/rate/provider failure,
        Synergy automatically switches to OpenRouter.
        """

        # -------------------------------------------------
        # OpenRouter already active
        # -------------------------------------------------

        if self.provider == "openrouter":

            return self._create_openrouter_interaction(
                input_data
            )

        # -------------------------------------------------
        # Try Gemini
        # -------------------------------------------------

        try:

            return self._create_gemini_interaction(
                input_data=input_data,
                previous_interaction_id=(
                    previous_interaction_id
                ),
            )

        except Exception as error:

            error_text = str(
                error
            ).lower()

            fallback_errors = [

                "429",

                "resource_exhausted",

                "quota",

                "rate limit",

                "too many requests",

                "503",

                "service unavailable",

                "timeout",

                "deadline exceeded",

                "temporarily unavailable",
            ]

            should_fallback = any(
                phrase in error_text
                for phrase in fallback_errors
            )

            if not should_fallback:

                raise

            self._activate_openrouter_fallback(
                reason=error
            )

            return self._create_openrouter_interaction(
                input_data
            )

    # =====================================================
    # SEND MESSAGE
    # =====================================================

    def send_message(
        self,
        user_message,
    ):

        self.current_user_message = (
            user_message
        )

        self.last_evidence = []

        self.pending_action = None

        # -------------------------------------------------
        # Store provider-independent history
        # -------------------------------------------------

        self.conversation_history.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        # -------------------------------------------------
        # If already using OpenRouter, add the message
        # there as well.
        # -------------------------------------------------

        if self.provider == "openrouter":

            if not self.openrouter_messages:

                self._initialize_openrouter_history()

            else:

                self.openrouter_messages.append(
                    {
                        "role": "user",
                        "content": user_message,
                    }
                )

        log_event(
            "USER_REQUEST",
            message=user_message,
        )

        # -------------------------------------------------
        # Start model interaction
        # -------------------------------------------------

        interaction = self._create_interaction(

            input_data=user_message,

            previous_interaction_id=(
                self.previous_interaction_id
            ),
        )

        self.previous_interaction_id = (
            interaction.id
        )

        log_event(
            "INTERACTION_CREATED",
            interaction_id=interaction.id,
            provider=self.provider,
        )

        return self._process_interaction(

            interaction=interaction,

            user_message=user_message,

            trace=[],

            evidence=[],
        )

    # =====================================================
    # PROCESS INTERACTION
    # =====================================================

    def _process_interaction(
        self,
        interaction,
        user_message,
        trace,
        evidence,
    ):

        for _ in range(
            MAX_AGENT_STEPS
        ):

            function_calls = [

                step

                for step in interaction.steps

                if step.type
                == "function_call"
            ]

            self.last_function_calls = (
                function_calls
            )

            # =================================================
            # NO TOOL CALL
            # =================================================

            if not function_calls:

                answer = (
                    interaction.output_text
                    or "Synergy completed the request."
                )

                self.last_evidence = evidence

                # -------------------------------------------------
                # AI verification only through the current Gemini
                # verifier implementation.
                # -------------------------------------------------

                if (

                    self.provider
                    == "gemini"

                    and needs_ai_verification(
                        answer,
                        evidence,
                    )
                ):

                    try:

                        verification = (
                            verify_response_with_ai(
                                self.client,
                                answer,
                                evidence,
                            )
                        )

                        log_event(
                            "AI_RESPONSE_VERIFICATION",
                            status=(
                                verification[
                                    "status"
                                ]
                            ),
                            issues=(
                                verification[
                                    "issues"
                                ]
                            ),
                        )

                        if (
                            verification[
                                "status"
                            ]
                            == "review"
                        ):

                            return {

                                "status":
                                    "verification_review",

                                "message": (
                                    "I found relevant information, "
                                    "but part of my response could "
                                    "not be confidently verified "
                                    "against the available "
                                    "company evidence."
                                ),

                                "trace":
                                    trace + [
                                        "AI verification flagged "
                                        "an unsupported claim",
                                    ],

                                "verification":
                                    verification,

                                "provider":
                                    self.provider,
                            }

                    except Exception as error:

                        log_event(
                            "AI_RESPONSE_VERIFICATION_FAILED",
                            error=str(error),
                        )

                        trace.append(
                            "AI verification unavailable"
                        )

                elif (

                    self.provider
                    == "openrouter"

                    and needs_ai_verification(
                        answer,
                        evidence,
                    )
                ):

                    trace.append(
                        "AI verification skipped "
                        "because fallback provider "
                        "is active"
                    )

                # -------------------------------------------------
                # Save final response
                # -------------------------------------------------

                self.conversation_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

                trace.append(
                    "Final response generated"
                )

                log_event(
                    "FINAL_RESPONSE_GENERATED",
                    provider=self.provider,
                )

                return {

                    "status":
                        "success",

                    "message":
                        answer,

                    "trace":
                        trace,

                    "provider":
                        self.provider,

                }

            # =================================================
            # PROCESS TOOL CALLS
            # =================================================

            function_results = []

            for step in function_calls:

                tool_name = (
                    step.name
                    .strip()
                    .lower()
                )

                arguments = step.arguments

                trace.append(
                    f"Tool requested: {tool_name}"
                )

                log_event(
                    "TOOL_REQUESTED",
                    tool=tool_name,
                    arguments=arguments,
                    provider=self.provider,
                )

                # -------------------------------------------------
                # POLICY
                # -------------------------------------------------

                policy = assess_action(
                    action_name=tool_name
                )

                # =================================================
                # HIGH-RISK ACTION
                # =================================================

                if (
                    policy["status"]
                    == "confirmation_required"
                ):

                    log_event(
                        "ACTION_AWAITING_APPROVAL",
                        tool=tool_name,
                        arguments=arguments,
                    )

                    self.pending_action = {

                        "interaction_id":
                            interaction.id,

                        "tool_name":
                            tool_name,

                        "arguments":
                            arguments,

                        "function_results":
                            function_results,

                        "trace":
                            trace.copy(),

                        "evidence":
                            evidence.copy(),

                        "user_message":
                            user_message,

                        "provider":
                            self.provider,

                        "tool_call_id":
                            step.id,
                    }

                    return {

                        "status":
                            "confirmation_required",

                        "message": (
                            "I can perform that action, "
                            "but I need your confirmation "
                            "first."
                        ),

                        "pending_action": {

                            "tool":
                                tool_name,

                            "arguments":
                                arguments,
                        },

                        "trace":
                            trace + [
                                "Action paused for "
                                "human approval",
                            ],

                        "provider":
                            self.provider,
                    }

                # =================================================
                # BLOCKED ACTION
                # =================================================

                if (
                    policy["status"]
                    == "blocked"
                ):

                    log_event(
                        "ACTION_BLOCKED",
                        tool=tool_name,
                        reason=policy["reason"],
                    )

                    return {

                        "status":
                            "blocked",

                        "message": (
                            "I can't perform that action "
                            "because it isn't an approved "
                            "Synergy capability."
                        ),

                        "trace":
                            trace + [
                                "Action blocked by policy",
                            ],

                        "provider":
                            self.provider,
                    }

                # =================================================
                # FIND PYTHON FUNCTION
                # =================================================

                function = (
                    TOOL_FUNCTIONS.get(
                        tool_name
                    )
                )

                if function is None:

                    error = (
                        f"Tool '{tool_name}' "
                        "is not registered."
                    )

                    log_event(
                        "TOOL_FAILED",
                        tool=tool_name,
                        error=error,
                    )

                    return {

                        "status":
                            "execution_failed",

                        "message": (
                            f"Synergy could not execute "
                            f"{tool_name}: {error}"
                        ),

                        "trace":
                            trace,

                        "provider":
                            self.provider,
                    }

                # =================================================
                # EXECUTE TOOL
                # =================================================

                try:

                    log_event(
                        "TOOL_EXECUTION_STARTED",
                        tool=tool_name,
                    )

                    result = function(
                        **arguments
                    )

                    if result is None:

                        raise RuntimeError(
                            "Tool returned no result."
                        )

                    log_event(
                        "TOOL_EXECUTED",
                        tool=tool_name,
                        result=result,
                    )

                    trace.append(
                        f"Tool succeeded: {tool_name}"
                    )

                    evidence.append(
                        str(result)
                    )

                    function_results.append({

                        "type":
                            "function_result",

                        "name":
                            tool_name,

                        "call_id":
                            step.id,

                        "result": [

                            {
                                "type":
                                    "text",

                                "text":
                                    json.dumps(
                                        result,
                                        ensure_ascii=False,
                                        default=str,
                                    ),
                            }

                        ],
                    })

                except Exception as error:

                    error_message = str(
                        error
                    )

                    log_event(
                        "TOOL_FAILED",
                        tool=tool_name,
                        error=error_message,
                    )

                    trace.append(
                        f"Tool failed: {tool_name}"
                    )

                    return {

                        "status":
                            "execution_failed",

                        "message": (
                            f"Synergy could not execute "
                            f"{tool_name}: "
                            f"{error_message}"
                        ),

                        "trace":
                            trace,

                        "provider":
                            self.provider,
                    }

            # =================================================
            # SEND TOOL RESULTS BACK TO MODEL
            # =================================================

            interaction = (
                self._create_interaction(

                    input_data=
                        function_results,

                    previous_interaction_id=
                        interaction.id,
                )
            )

            self.previous_interaction_id = (
                interaction.id
            )

            log_event(
                "TOOL_RESULTS_RETURNED",
                interaction_id=interaction.id,
                provider=self.provider,
            )

            trace.append(
                "Tool results returned to model"
            )

        return {

            "status":
                "execution_failed",

            "message":
                (
                    "Synergy reached its maximum "
                    "agent steps."
                ),

            "trace":
                trace,

            "provider":
                self.provider,
        }

    # =====================================================
    # APPROVE PENDING ACTION
    # =====================================================

    def approve_pending_action(self):

        if not self.pending_action:

            return {

                "status":
                    "error",

                "message":
                    (
                        "There is no pending action "
                        "to approve."
                    ),
            }

        pending = (
            self.pending_action
        )

        self.pending_action = None

        tool_name = pending[
            "tool_name"
        ]

        arguments = pending[
            "arguments"
        ]

        tool_call_id = pending[
            "tool_call_id"
        ]

        trace = pending.get(
            "trace",
            [],
        )

        evidence = pending.get(
            "evidence",
            [],
        )

        provider = pending.get(
            "provider",
            self.provider,
        )

        try:

            policy = assess_action(
                action_name=tool_name
            )

            if (
                policy["status"]
                != "confirmation_required"
            ):

                return {

                    "status":
                        "blocked",

                    "message":
                        (
                            "This action is no longer "
                            "eligible for approval."
                        ),

                    "trace":
                        trace,
                }

            function = (
                TOOL_FUNCTIONS.get(
                    tool_name
                )
            )

            if function is None:

                return {

                    "status":
                        "execution_failed",

                    "message":
                        (
                            f"Tool '{tool_name}' "
                            "is not registered."
                        ),

                    "trace":
                        trace,
                }

            log_event(
                "ACTION_APPROVED",
                tool=tool_name,
                arguments=arguments,
                provider=provider,
            )

            result = function(
                **arguments
            )

            if result is None:

                raise RuntimeError(
                    "Tool returned no result."
                )

            log_event(
                "TOOL_EXECUTED",
                tool=tool_name,
                result=result,
            )

            trace.append(
                f"Action approved: {tool_name}"
            )

            trace.append(
                f"Tool succeeded: {tool_name}"
            )

            evidence.append(
                str(result)
            )

            function_result = {

                "type":
                    "function_result",

                "name":
                    tool_name,

                "call_id":
                    tool_call_id,

                "result": [

                    {
                        "type":
                            "text",

                        "text":
                            json.dumps(
                                result,
                                ensure_ascii=False,
                                default=str,
                            ),
                    }

                ],
            }

            # -------------------------------------------------
            # Continue Gemini conversation
            # -------------------------------------------------

            if provider == "gemini":

                try:

                    interaction = (
                        self._create_gemini_interaction(

                            input_data=[
                                function_result
                            ],

                            previous_interaction_id=
                                pending[
                                    "interaction_id"
                                ],
                        )
                    )

                except Exception as error:

                    # If Gemini quota fails here,
                    # switch to OpenRouter.

                    self._activate_openrouter_fallback(
                        reason=error
                    )

                    interaction = (
                        self._create_openrouter_interaction(
                            [
                                function_result
                            ]
                        )
                    )

                self.previous_interaction_id = (
                    interaction.id
                )

                return self._process_interaction(

                    interaction=interaction,

                    user_message=pending[
                        "user_message"
                    ],

                    trace=trace,

                    evidence=evidence,
                )

            # -------------------------------------------------
            # Continue OpenRouter conversation
            # -------------------------------------------------

            interaction = (
                self._create_openrouter_interaction(
                    [
                        function_result
                    ]
                )
            )

            self.previous_interaction_id = (
                interaction.id
            )

            return self._process_interaction(

                interaction=interaction,

                user_message=pending[
                    "user_message"
                ],

                trace=trace,

                evidence=evidence,
            )

        except Exception as error:

            error_message = str(
                error
            )

            log_event(
                "TOOL_FAILED",
                tool=tool_name,
                error=error_message,
            )

            return {

                "status":
                    "execution_failed",

                "message":
                    (
                        f"Synergy could not execute "
                        f"{tool_name}: "
                        f"{error_message}"
                    ),

                "trace":
                    trace,
            }

    # =====================================================
    # CANCEL PENDING ACTION
    # =====================================================

    def cancel_pending_action(self):

        if not self.pending_action:

            return {

                "status":
                    "error",

                "message":
                    (
                        "There is no pending action "
                        "to cancel."
                    ),
            }

        tool_name = (
            self.pending_action[
                "tool_name"
            ]
        )

        self.pending_action = None

        log_event(
            "ACTION_CANCELLED",
            tool=tool_name,
        )

        return {

            "status":
                "cancelled",

            "message":
                (
                    "Understood. I did not execute "
                    "that action."
                ),

            "trace": [
                f"Action cancelled: {tool_name}"
            ],
        }

