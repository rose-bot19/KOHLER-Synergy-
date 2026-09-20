import json
import os
import shutil
import uuid
from datetime import datetime


DATA_DIR = "data"


def _ensure_data_dir():
    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )


def _load_json(
    filename,
    default,
):
    _ensure_data_dir()

    path = os.path.join(
        DATA_DIR,
        filename,
    )

    if not os.path.exists(path):
        return default

    try:

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError,
    ):

        return default


def _save_json(
    filename,
    data,
):
    _ensure_data_dir()

    path = os.path.join(
        DATA_DIR,
        filename,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def _timestamp():
    return datetime.now().astimezone().isoformat()


# =========================================================
# HIGH-RISK: SEND EMAIL
# =========================================================

def send_email(
    recipient,
    subject,
    body,
):
    """
    Mock enterprise email connector.

    IMPORTANT:
    This does NOT connect to Gmail, Outlook, or any
    external mailbox.

    It records the approved email in data/outbox.json
    so the enterprise-action workflow can be demonstrated.
    """

    emails = _load_json(
        "outbox.json",
        [],
    )

    email_id = (
        "EMAIL-"
        + uuid.uuid4().hex[:8].upper()
    )

    email = {

        "email_id":
            email_id,

        "sender":
            "KOHLER Synergy Demo",

        "recipient":
            recipient,

        "subject":
            subject,

        "body":
            body,

        "status":
            "simulated_sent",

        "connector":
            "mock_email_connector",

        "created_at":
            _timestamp(),
    }

    emails.append(
        email
    )

    _save_json(
        "outbox.json",
        emails,
    )

    return {

        "status":
            "success",

        "message":
            (
                f"Mock email {email_id} "
                "recorded successfully."
            ),

        "note":
            (
                "This is a demo-only mock email "
                "connector. No real email was sent."
            ),

        "email":
            email,
    }


# =========================================================
# HIGH-RISK: UPDATE CUSTOMER RECORD
# =========================================================

def update_customer_record(
    customer_name,
    fields,
):
    """
    Mock enterprise customer-record update.
    """

    customers = _load_json(
        "customers.json",
        [],
    )

    customer = None

    for item in customers:

        if (
            str(
                item.get(
                    "name",
                    "",
                )
            ).lower()
            == str(
                customer_name
            ).lower()
        ):

            customer = item
            break

    if customer is None:

        customer = {

            "customer_id":
                (
                    "CUS-"
                    + uuid.uuid4().hex[:8].upper()
                ),

            "name":
                customer_name,
        }

        customers.append(
            customer
        )

    if not isinstance(
        fields,
        dict,
    ):

        fields = {
            "notes":
                str(fields)
        }

    for key, value in fields.items():

        customer[key] = value

    customer[
        "updated_at"
    ] = _timestamp()

    _save_json(
        "customers.json",
        customers,
    )

    return {

        "status":
            "success",

        "message":
            (
                f"Customer record for "
                f"{customer_name} "
                "updated successfully."
            ),

        "customer":
            customer,
    }


# =========================================================
# HIGH-RISK: DELETE RECORD
# =========================================================

def delete_record(
    record_type,
    record_id,
):
    """
    Mock enterprise deletion.
    """

    records = _load_json(
        "enterprise_records.json",
        [],
    )

    remaining = []

    deleted = None

    for record in records:

        matches_type = (
            str(
                record.get(
                    "type",
                    "",
                )
            ).lower()
            == str(
                record_type
            ).lower()
        )

        matches_id = (
            str(
                record.get(
                    "id",
                    "",
                )
            ).lower()
            == str(
                record_id
            ).lower()
        )

        if (
            matches_type
            and matches_id
        ):

            deleted = record

        else:

            remaining.append(
                record
            )

    if deleted is None:

        return {

            "status":
                "not_found",

            "message":
                (
                    f"No {record_type} "
                    f"record with ID "
                    f"{record_id} was found."
                ),
        }

    _save_json(
        "enterprise_records.json",
        remaining,
    )

    return {

        "status":
            "success",

        "message":
            (
                f"{record_type} record "
                f"{record_id} deleted "
                "successfully."
            ),

        "deleted_record":
            deleted,
    }


# =========================================================
# HIGH-RISK: MAINTENANCE DISPATCH
# =========================================================

def create_maintenance_dispatch(
    customer,
    location,
    issue,
    priority="normal",
):
    """
    Mock facilities / maintenance dispatch.
    """

    dispatches = _load_json(
        "maintenance_dispatches.json",
        [],
    )

    dispatch_id = (
        "MD-"
        + uuid.uuid4().hex[:8].upper()
    )

    dispatch = {

        "dispatch_id":
            dispatch_id,

        "customer":
            customer,

        "location":
            location,

        "issue":
            issue,

        "priority":
            priority,

        "status":
            "created",

        "connector":
            "mock_maintenance_connector",

        "created_at":
            _timestamp(),
    }

    dispatches.append(
        dispatch
    )

    _save_json(
        "maintenance_dispatches.json",
        dispatches,
    )

    return {

        "status":
            "success",

        "message":
            (
                f"Maintenance dispatch "
                f"{dispatch_id} created "
                "successfully."
            ),

        "dispatch":
            dispatch,
    }


# =========================================================
# LOW-RISK: STORE DOCUMENT
# =========================================================

def store_document(
    file_path,
    category,
):
    """
    Store an approved company document in the
    selected knowledge-base category.
    """

    allowed_categories = {
        "policies",
        "products",
        "support",
        "projects",
        "facilities",
        "finance",
        "compliance",
    }

    category = str(
        category
    ).strip().lower()

    if category not in allowed_categories:

        return {

            "status":
                "error",

            "message":
                (
                    f"Unknown knowledge "
                    f"category: {category}"
                ),
        }

    if not os.path.exists(
        file_path
    ):

        return {

            "status":
                "error",

            "message":
                (
                    f"File not found: "
                    f"{file_path}"
                ),
        }

    destination_dir = os.path.join(
        "knowledge",
        category,
    )

    os.makedirs(
        destination_dir,
        exist_ok=True,
    )

    filename = os.path.basename(
        file_path
    )

    destination = os.path.join(
        destination_dir,
        filename,
    )

    shutil.copy2(
        file_path,
        destination,
    )

    return {

        "status":
            "success",

        "message":
            (
                f"Document stored in "
                f"the {category} "
                "knowledge category."
            ),

        "category":
            category,

        "path":
            destination,
    }