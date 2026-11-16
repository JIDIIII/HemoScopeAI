from uuid import UUID

from fastapi import APIRouter

from app.schemas.analysis import SessionMetadata
from app.schemas.errors import ErrorResponse
from app.services.session_service import get_session_metadata

router = APIRouter(tags=["sessions"])


@router.get(
    "/session/{session_id}",
    response_model=SessionMetadata,
    responses={501: {"model": ErrorResponse}},
)
async def get_session(session_id: UUID) -> SessionMetadata:
    return get_session_metadata(str(session_id))
