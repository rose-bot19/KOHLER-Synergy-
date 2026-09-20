def validate_execution(tool_name, result):
    """
    Validate a tool execution result before it is treated as successful.
    """

    if result is None:
        return {
            "valid": False,
            "reason": "Tool returned no result.",
        }

    if isinstance(result, dict):

        status = result.get("status")

        if status == "failed":
            return {
                "valid": False,
                "reason": result.get(
                    "error",
                    "Tool execution failed."
                ),
            }

    return {
        "valid": True,
        "reason": "Tool returned a result.",
    }


def build_failure_response(tool_name, error):
    """Create a safe response when a tool fails."""

    return (
        f"I couldn't complete the '{tool_name}' action. "
        f"The system reported: {error}. "
        "No successful completion will be reported."
    )