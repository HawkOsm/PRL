"""The heuristic router: cheap rules that need no language model."""

# A session is active and the message is shorter than this: send it on, no LLM call.
SHORT_FOLLOW_UP_CHARS = 40


def route(message: str, session_active: bool) -> str:
    """Decide what to do with a message using plain rules only."""
    text = message.strip()
    if text.startswith("/"):
        return "META"  # a command such as /help or /quick
    if session_active and len(text) < SHORT_FOLLOW_UP_CHARS:
        return "PASSTHROUGH"  # a short follow-up flies through untouched
    # Unsure: the failsafe direction is PASSTHROUGH. In M4 the LLM takes over here.
    return "PASSTHROUGH"
