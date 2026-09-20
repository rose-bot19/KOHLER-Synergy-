READ_ONLY_ACTIONS = {
    "search_knowledge_base",
    "check_warranty",
    "get_ticket",
    "get_product_information",
    "get_project_status",
    "classify_new_document",
    "delegate_complex_task",
}

LOW_RISK_ACTIONS = {
    "create_support_ticket",
    "store_document",
}

HIGH_RISK_ACTIONS = {
    "send_email",
    "update_customer_record",
    "delete_record",
    "create_maintenance_dispatch",
}


def normalize_action(action_name):

    return action_name.strip().lower()


def assess_action(action_name):

    action_name = normalize_action(
        action_name
    )

    if action_name in READ_ONLY_ACTIONS:

        return {
            "status": "allowed",
            "reason": "Read-only action",
        }


    if action_name in LOW_RISK_ACTIONS:

        return {
            "status": "allowed",
            "reason": (
                "Low-risk action. "
                "The agent's tool request "
                "represents its interpretation "
                "of the user's request."
            ),
        }


    if action_name in HIGH_RISK_ACTIONS:

        return {
            "status": "confirmation_required",
            "reason": (
                "High-risk action requires "
                "human approval."
            ),
        }


    return {
        "status": "blocked",
        "reason": (
            "Unknown or unapproved action."
        ),
    }