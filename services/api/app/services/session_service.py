from app.core.errors import APIError
from app.schemas.analysis import SessionMetadata


def get_session_metadata(session_id: str) -> SessionMetadata:
    """Server-side session storage is deliberately disabled in this scaffold."""
    del session_id
    raise APIError(
        501,
        "server_sessions_disabled",
        "Research history is local-first. Server-side session persistence is not configured.",
    )
