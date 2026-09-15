from backend.database.repositories.conversation import ConversationRepository
from backend.domain.conversation import ConversationTurn
from backend.domain.enums import SessionStatus
from backend.models.conversation import ConversationTurnDocument
from backend.services.clinical_session import ClinicalSessionService


class ConversationService:
    def __init__(
        self,
        repository: ConversationRepository,
        session_service: ClinicalSessionService | None = None,
    ) -> None:
        self.repository = repository
        self.session_service = session_service

    async def get_turn(self, turn_id: str) -> ConversationTurn | None:
        document = await self.repository.get_turn(turn_id)
        if document is None:
            return None
        return self._to_domain(document)

    async def get_session_turns(self, session_id: str) -> list[ConversationTurn]:
        documents = await self.repository.get_session_turns(session_id)
        return [self._to_domain(document) for document in documents]

    async def add_turn(self, turn: ConversationTurn) -> ConversationTurn:
        document = self._to_document(turn)
        await self.repository.create_turn(document)
        return turn

    async def submit_turn(self, turn: ConversationTurn) -> ConversationTurn:
        if self.session_service is None:
            raise ValueError(
                "Session service is required to submit a conversation turn")

        session = await self.session_service.get_session(turn.session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status not in {
            SessionStatus.CONSENTED,
            SessionStatus.HISTORY_IN_PROGRESS,
        }:
            raise ValueError(
                "Session must be consented or have history in progress",
            )

        if session.status == SessionStatus.CONSENTED:
            updated_session = await self.session_service.transition_session(
                turn.session_id,
                SessionStatus.HISTORY_IN_PROGRESS,
            )

            if updated_session is None:
                raise ValueError(
                    "Clinical session could not enter history state",
                )

        return await self.add_turn(turn)

    @staticmethod
    def _to_domain(document: ConversationTurnDocument) -> ConversationTurn:
        return ConversationTurn(
            turn_id=document.turn_id,
            session_id=document.session_id,
            speaker=document.speaker,
            input_type=document.input_type,
            content=document.content,
            language=document.language,
            media_reference=document.media_reference,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def _to_document(turn: ConversationTurn) -> ConversationTurnDocument:
        return ConversationTurnDocument(
            turn_id=turn.turn_id,
            session_id=turn.session_id,
            speaker=turn.speaker,
            input_type=turn.input_type,
            content=turn.content,
            language=turn.language,
            media_reference=turn.media_reference,
            created_at=turn.created_at,
            updated_at=turn.updated_at,
        )
