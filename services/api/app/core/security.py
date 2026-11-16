from uuid import uuid4


def create_request_id() -> str:
    """Create a server-owned opaque request identifier for error correlation."""
    return str(uuid4())
