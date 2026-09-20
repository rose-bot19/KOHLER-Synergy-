import json
import os
import tempfile
import uuid
from datetime import datetime


DATA_DIR = "data"
CONVERSATIONS_FILE = os.path.join(
    DATA_DIR,
    "conversations.json",
)


def _now():
    return datetime.now().astimezone().isoformat()


def _ensure_storage():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(CONVERSATIONS_FILE):
        with open(
            CONVERSATIONS_FILE,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                [],
                file,
                indent=2,
            )


def _load_all():
    _ensure_storage()

    try:
        with open(
            CONVERSATIONS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except (
        json.JSONDecodeError,
        OSError,
    ):
        pass

    return []


def _save_all(conversations):
    _ensure_storage()

    directory = os.path.dirname(
        CONVERSATIONS_FILE
    )

    fd, temp_path = tempfile.mkstemp(
        dir=directory,
        suffix=".tmp",
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                conversations,
                file,
                indent=2,
                ensure_ascii=False,
            )

        os.replace(
            temp_path,
            CONVERSATIONS_FILE,
        )

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _make_json_safe(value):
    """
    Convert common Python objects into
    JSON-safe values.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if isinstance(value, dict):
        return {
            str(key): _make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _make_json_safe(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            _make_json_safe(item)
            for item in value
        ]

    return str(value)


def create_conversation(title="New Conversation"):
    conversations = _load_all()

    conversation = {
        "id": f"conv-{uuid.uuid4().hex[:10]}",
        "title": title,
        "saved": False,
        "created_at": _now(),
        "updated_at": _now(),
        "previous_interaction_id": None,
        "messages": [],
    }

    conversations.append(conversation)

    _save_all(conversations)

    return conversation


def get_conversation(conversation_id):
    conversations = _load_all()

    for conversation in conversations:
        if conversation["id"] == conversation_id:
            return conversation

    return None


def get_recent_conversations(limit=10):
    conversations = _load_all()

    conversations.sort(
        key=lambda item: item.get(
            "updated_at",
            "",
        ),
        reverse=True,
    )

    return conversations[:limit]


def get_saved_conversations():
    conversations = _load_all()

    saved = [
        conversation
        for conversation in conversations
        if conversation.get("saved") is True
    ]

    saved.sort(
        key=lambda item: item.get(
            "updated_at",
            "",
        ),
        reverse=True,
    )

    return saved


def update_conversation(
    conversation_id,
    **updates,
):
    conversations = _load_all()

    for conversation in conversations:

        if conversation["id"] == conversation_id:

            for key, value in updates.items():
                conversation[key] = _make_json_safe(
                    value
                )

            conversation["updated_at"] = _now()

            _save_all(conversations)

            return conversation

    return None


def append_message(
    conversation_id,
    role,
    content,
    result=None,
):
    conversations = _load_all()

    for conversation in conversations:

        if conversation["id"] != conversation_id:
            continue

        message = {
            "role": role,
            "content": str(content),
            "timestamp": _now(),
        }

        if result is not None:
            message["result"] = _make_json_safe(
                result
            )

        conversation["messages"].append(
            message
        )

        if (
            conversation["title"]
            == "New Conversation"
            and role == "user"
        ):
            cleaned = str(content).strip()

            if len(cleaned) > 55:
                cleaned = (
                    cleaned[:55].rstrip()
                    + "..."
                )

            conversation["title"] = (
                cleaned
                if cleaned
                else "New Conversation"
            )

        conversation["updated_at"] = _now()

        _save_all(conversations)

        return conversation

    return None


def set_saved(
    conversation_id,
    saved=True,
):
    return update_conversation(
        conversation_id,
        saved=saved,
    )


def set_previous_interaction_id(
    conversation_id,
    interaction_id,
):
    return update_conversation(
        conversation_id,
        previous_interaction_id=interaction_id,
    )