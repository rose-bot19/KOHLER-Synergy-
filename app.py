import json

import streamlit as st

from orchestrator import SynergyOrchestrator

from conversation_store import (
    append_message,
    create_conversation,
    get_conversation,
    get_recent_conversations,
    get_saved_conversations,
    set_saved,
)


#PAGE CONFIG

st.set_page_config(
    page_title="KOHLER Synergy",
    page_icon="◆",
    layout="wide",
)


#SESSION STATE


if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = (
        SynergyOrchestrator()
    )

if "conversation_id" not in st.session_state:

    recent = get_recent_conversations(
        limit=1
    )

    if recent:
        st.session_state.conversation_id = (
            recent[0]["id"]
        )

    else:
        conversation = create_conversation()

        st.session_state.conversation_id = (
            conversation["id"]
        )


if "messages" not in st.session_state:

    conversation = get_conversation(
        st.session_state.conversation_id
    )

    if conversation:

        st.session_state.messages = (
            conversation.get(
                "messages",
                [],
            )
        )

        st.session_state.orchestrator.set_history(
            st.session_state.messages
        )

    else:

        st.session_state.messages = []


if "pending_action" not in st.session_state:
    st.session_state.pending_action = None


if "last_result" not in st.session_state:
    st.session_state.last_result = None


#CONVERSATION HELPERS

def load_conversation(
    conversation_id,
):

    conversation = get_conversation(
        conversation_id
    )

    if not conversation:
        return

    st.session_state.conversation_id = (
        conversation_id
    )

    st.session_state.messages = (
        conversation.get(
            "messages",
            [],
        )
    )

    st.session_state.orchestrator.set_history(
        st.session_state.messages
    )

    st.session_state.pending_action = None
    st.session_state.last_result = None


def start_new_conversation():

    conversation = create_conversation()

    st.session_state.conversation_id = (
        conversation["id"]
    )

    st.session_state.messages = []

    st.session_state.orchestrator.set_history(
        []
    )

    st.session_state.pending_action = None
    st.session_state.last_result = None


#RESULT HELPERS

def result_to_text(result):

    if result is None:

        return "Synergy returned no response."

    if isinstance(result, str):

        return result

    if isinstance(result, dict):

        for key in [
            "message",
            "response",
            "answer",
            "final_response",
            "output",
        ]:

            value = result.get(
                key
            )

            if (
                isinstance(
                    value,
                    str,
                )
                and value.strip()
            ):

                return value

        return json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    return str(result)


def extract_pending_action(
    result,
):

    if not isinstance(
        result,
        dict,
    ):
        return None

    status = str(
        result.get(
            "status",
            "",
        )
    ).lower()


    if status in {
        "confirmation_required",
        "approval_required",
        "pending_approval",
        "awaiting_approval",
    }:

        return (
            result.get(
                "pending_action"
            )
            or result.get(
                "action"
            )
            or result.get(
                "tool"
            )
        )

    if result.get(
        "approval_required"
    ) is True:

        return (
            result.get(
                "pending_action"
            )
            or result.get(
                "action"
            )
            or result.get(
                "tool"
            )
        )

    return None


def extract_sources(
    result,
):

    if not isinstance(
        result,
        dict,
    ):
        return []

    sources = result.get(
        "sources",
        [],
    )

    if isinstance(
        sources,
        list,
    ):
        return sources

    return [sources]


def extract_activity(
    result,
):

    if not isinstance(
        result,
        dict,
    ):
        return {}

    activity = {}

    for key in [
        "activity",
        "trace",
        "events",
        "tool_results",
        "verification",
        "sources",
    ]:

        if result.get(
            key
        ):

            activity[key] = (
                result[key]
            )

    return activity


#DISPLAY HELPERS

def display_activity(
    result,
):

    activity = extract_activity(
        result
    )

    with st.expander(
        "Agent Activity",
        expanded=False,
    ):

        if not activity:

            st.caption(
                "No execution trace was returned."
            )

            return

        for key, value in activity.items():

            st.markdown(
                f"**{key.replace('_', ' ').title()}**"
            )

            if isinstance(
                value,
                (
                    dict,
                    list,
                ),
            ):

                st.json(value)

            else:

                st.write(value)


def display_sources(
    result,
):

    sources = extract_sources(
        result
    )

    if not sources:
        return

    with st.expander(
        "Knowledge Sources",
        expanded=False,
    ):

        for source in sources:

            if isinstance(
                source,
                dict,
            ):

                name = (
                    source.get(
                        "source"
                    )
                    or source.get(
                        "name"
                    )
                    or source.get(
                        "file"
                    )
                    or "Knowledge source"
                )

                st.markdown(
                    f"**{name}**"
                )

                content = (
                    source.get(
                        "content"
                    )
                    or source.get(
                        "text"
                    )
                )

                if content:

                    st.caption(
                        str(content)
                    )

            else:

                st.markdown(
                    f"**{source}**"
                )


def display_pending_action(
    pending_action,
):

    if not pending_action:
        return

    st.warning(
        "Human approval required before this action can execute."
    )

    #EMAIL DRAFT

    if isinstance(
        pending_action,
        dict,
    ):

        tool_name = (
            pending_action.get(
                "tool"
            )
            or pending_action.get(
                "tool_name"
            )
        )

        arguments = (
            pending_action.get(
                "arguments",
                {}
            )
        )

        if tool_name == "send_email":

            st.markdown(
                "### Email Draft"
            )

            st.caption(
                "This is only a draft preview. "
                "Nothing will be sent until you approve it."
            )

            recipient = arguments.get(
                "recipient",
                "Not specified",
            )

            subject = arguments.get(
                "subject",
                "(No subject)",
            )

            body = arguments.get(
                "body",
                "",
            )

            st.markdown(
                f"**To:** {recipient}"
            )

            st.markdown(
                f"**Subject:** {subject}"
            )

            st.text_area(
                "Message",
                value=str(body),
                height=180,
                disabled=True,
            )

            st.caption(
                "Sending mode: KOHLER Synergy Demo "
                "(mock connector; no real mailbox is connected)"
            )

            return

        #OTHER HIGH-RISK ACTIONS

        st.markdown(
            "### Pending Action"
        )

        st.json(
            pending_action
        )

    else:

        st.markdown(
            f"### Pending Action\n`{pending_action}`"
        )


#SIDEBAR

with st.sidebar:

    st.title(
        "◆ KOHLER Synergy"
    )

    st.caption(
        "Adaptive Enterprise AI Agent"
    )

    st.divider()

    if st.button(
        "+ New Chat",
        type="primary",
        use_container_width=True,
    ):

        start_new_conversation()

        st.rerun()

    current_conversation = (
        get_conversation(
            st.session_state.conversation_id
        )
    )

    if current_conversation:

        st.divider()

        st.markdown(
            "### Current Chat"
        )

        st.caption(
            current_conversation.get(
                "title",
                "New Conversation",
            )
        )

        if current_conversation.get(
            "saved",
            False,
        ):

            st.success(
                "Saved"
            )

        else:

            if st.button(
                "Save Chat",
                use_container_width=True,
            ):

                set_saved(
                    st.session_state.conversation_id,
                    True,
                )

                st.rerun()

    st.divider()

    st.markdown(
        "### Saved Conversations"
    )

    saved_conversations = (
        get_saved_conversations()
    )

    if not saved_conversations:

        st.caption(
            "No saved conversations yet."
        )

    else:

        for conversation in saved_conversations:

            title = conversation.get(
                "title",
                "Untitled Chat",
            )

            if len(title) > 32:

                title = (
                    title[:32].rstrip()
                    + "..."
                )

            if st.button(
                f"◆ {title}",
                key=(
                    f"saved_"
                    f"{conversation['id']}"
                ),
                use_container_width=True,
            ):

                load_conversation(
                    conversation["id"]
                )

                st.rerun()

    st.divider()

    st.markdown(
        "### Recent Conversations"
    )

    recent_conversations = (
        get_recent_conversations(
            limit=8
        )
    )

    for conversation in recent_conversations:

        title = conversation.get(
            "title",
            "New Conversation",
        )

        if len(title) > 32:

            title = (
                title[:32].rstrip()
                + "..."
            )

        is_current = (
            conversation["id"]
            == st.session_state.conversation_id
        )

        label = (
            "● "
            if is_current
            else ""
        ) + title

        if st.button(
            label,
            key=(
                f"recent_"
                f"{conversation['id']}"
            ),
            use_container_width=True,
        ):

            load_conversation(
                conversation["id"]
            )

            st.rerun()

    st.divider()

    st.markdown(
        "### Capabilities"
    )

    st.write(
        "Knowledge retrieval"
    )

    st.write(
        "Warranty intelligence"
    )

    st.write(
        "Support ticket actions"
    )

    st.write(
        "Conversational memory"
    )

    st.write(
        "Approval-aware actions"
    )

    st.write(
        "Enterprise orchestration"
    )

    st.write(
        "Provider fallback"
    )


#MAIN HEADER

st.title(
    "◆ KOHLER Synergy"
)

st.markdown(
    """
**One AI layer across knowledge, support, actions and enterprise workflows.**

Ask naturally. Synergy determines when to retrieve information,
when to use a tool, when approval is needed, and what useful next
step to suggest.
"""
)

st.divider()


#APPROVAL PANEL

if st.session_state.pending_action:

    display_pending_action(
        st.session_state.pending_action
    )

    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Approve & Execute",
            type="primary",
            use_container_width=True,
        ):

            with st.spinner(
                "Executing approved action..."
            ):

                result = (
                    st.session_state.orchestrator
                    .approve_pending_action()
                )

            st.session_state.pending_action = None

            st.session_state.last_result = (
                result
            )

            response = result_to_text(
                result
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response,
                    "result": result,
                }
            )

            append_message(
                st.session_state.conversation_id,
                "assistant",
                response,
                result,
            )

            st.rerun()

    with col2:

        if st.button(
            "Cancel",
            use_container_width=True,
        ):

            result = (
                st.session_state.orchestrator
                .cancel_pending_action()
            )

            st.session_state.pending_action = None

            st.session_state.last_result = (
                result
            )

            response = result_to_text(
                result
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response,
                    "result": result,
                }
            )

            append_message(
                st.session_state.conversation_id,
                "assistant",
                response,
                result,
            )

            st.rerun()


#CHAT HISTORY

for message in st.session_state.messages:

    role = message[
        "role"
    ]

    with st.chat_message(
        role
    ):

        st.markdown(
            message[
                "content"
            ]
        )

        if role == "assistant":

            result = message.get(
                "result"
            )

            if result:

                display_activity(
                    result
                )

                display_sources(
                    result
                )


#CHAT INPUT

user_message = st.chat_input(
    "Ask KOHLER Synergy anything..."
)


if user_message:

    #SAVE USER MESSAGE

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    append_message(
        st.session_state.conversation_id,
        "user",
        user_message,
    )

    with st.chat_message(
        "user"
    ):

        st.markdown(
            user_message
        )

    #RUN SYNERGY

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Synergy is working..."
        ):

            try:

                result = (
                    st.session_state.orchestrator
                    .send_message(
                        user_message
                    )
                )

            except Exception as error:

                result = {
                    "status": "error",
                    "message": (
                        "Synergy encountered an error."
                    ),
                    "error": str(error),
                }

        st.session_state.last_result = (
            result
        )

        response = result_to_text(
            result
        )

        st.markdown(
            response
        )

        display_activity(
            result
        )

        display_sources(
            result
        )

    #SAVE ASSISTANT RESPONSE

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
            "result": result,
        }
    )

    append_message(
        st.session_state.conversation_id,
        "assistant",
        response,
        result,
    )

    #DETECT APPROVAL

    pending_action = (
        extract_pending_action(
            result
        )
    )

    st.session_state.pending_action = (
        pending_action
    )

    st.rerun()
