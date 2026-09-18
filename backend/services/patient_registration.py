import hashlib

from fastapi import UploadFile
from pymongo.errors import DuplicateKeyError

from backend.domain.clinical_session import ClinicalSession
from backend.domain.common import utc_now
from backend.domain.conversation import ConversationTurn
from backend.domain.document import Document
from backend.domain.enums import (
    ConsentStatus,
    ConversationInputType,
    DocumentStatus,
    DocumentType,
    SessionStatus,
    Speaker,
    VerificationStatus,
)
from backend.domain.patient import Patient
from backend.integrations.storage import LocalStorage
from backend.services.clinical_session import ClinicalSessionService
from backend.services.conversation import ConversationService
from backend.services.document import DocumentService
from backend.services.ephemeral_identity import EphemeralIdentityService
from backend.services.patient import PatientService
from backend.services.verification import VerificationService


class PatientRegistrationService:
    def __init__(
        self,
        session_service: ClinicalSessionService,
        patient_service: PatientService,
        verification_service: VerificationService,
        conversation_service: ConversationService,
        document_service: DocumentService,
        storage: LocalStorage,
        ephemeral_identity_service: EphemeralIdentityService,
    ) -> None:
        self.session_service = session_service
        self.patient_service = patient_service
        self.verification_service = verification_service
        self.conversation_service = conversation_service
        self.document_service = document_service
        self.storage = storage
        self.ephemeral_identity_service = ephemeral_identity_service

    async def submit(
        self,
        draft_id: str,
        verification_token: str,
        identity_method: str,
        identity_identifier: str,
        consent_version: str,
        conversation_turns: list[dict],
        documents: list[dict],
        files: list[UploadFile],
        department_id: str,
    ) -> tuple[ClinicalSession, Patient, str]:
        verification = (
            await self.ephemeral_identity_service.get_verified_identity(
                draft_id,
                verification_token,
                identity_method,
                identity_identifier,
            )
        )

        if consent_version != "1.0":
            raise ValueError("Unsupported consent version")

        if len(documents) != len(files):
            raise ValueError(
                "Document metadata does not match uploaded files",
            )

        existing_patient = await self.patient_service.get_by_identity(
            identity_method,
            identity_identifier,
        )

        if (
            existing_patient is None
            and verification.result.patient_id is not None
        ):
            existing_patient = await self.patient_service.get_patient(
                verification.result.patient_id,
            )

        visit_type = (
            "RETURNING_VISIT"
            if existing_patient is not None
            else "FIRST_VISIT"
        )

        session_id = f"sess_{self._stable_id(draft_id)}"
        session = await self.session_service.get_session(session_id)

        if session is None:
            now = utc_now()

            session = ClinicalSession(
                session_id=session_id,
                patient_id="unverified",
                department_id=department_id,
                status=SessionStatus.IDENTIFYING,
                verification_status=VerificationStatus.VERIFIED,
                consent_status=ConsentStatus.PENDING,
                created_at=now,
                updated_at=now,
            )

            try:
                await self.session_service.create_session(session)
            except DuplicateKeyError:
                existing_session = await self.session_service.get_session(
                    session_id,
                )

                if existing_session is None:
                    raise

                session = existing_session

        if session.status in {
            SessionStatus.CANCELLED,
            SessionStatus.ABANDONED,
            SessionStatus.ERROR,
        }:
            raise ValueError("Registration draft is no longer active")

        if session.patient_id == "unverified":
            await self.session_service.set_verification_status(
                session_id,
                VerificationStatus.VERIFIED,
            )

            await self.verification_service.persist_identity(
                session_id,
                identity_method,
                identity_identifier,
            )
        else:
            visit_type = "RETURNING_VISIT"

        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session could not be loaded")

        if session.consent_status != ConsentStatus.GRANTED:
            if session.status != SessionStatus.IDENTIFYING:
                raise ValueError(
                    "Clinical session is not ready to record consent",
                )

            updated_session = await self.session_service.set_consent(
                session_id,
                ConsentStatus.GRANTED,
            )

            if updated_session is None:
                raise ValueError(
                    "Clinical session could not be consented",
                )

            updated_session = await self.session_service.transition_session(
                session_id,
                SessionStatus.CONSENTED,
            )

            if updated_session is None:
                raise ValueError(
                    "Clinical session could not enter consented state",
                )

            session = updated_session

        existing_turns = {
            turn.turn_id
            for turn in await self.conversation_service.get_session_turns(
                session_id,
            )
        }

        for turn_index, turn_data in enumerate(conversation_turns):
            content = str(turn_data.get("content", "")).strip()

            if not content:
                continue

            turn_id = self._stable_resource_id(
                "turn",
                draft_id,
                str(turn_data.get("local_id", turn_index)),
            )

            if turn_id in existing_turns:
                continue

            turn = ConversationTurn(
                turn_id=turn_id,
                session_id=session_id,
                speaker=Speaker.PATIENT,
                input_type=ConversationInputType(
                    str(turn_data.get("input_type", "TEXT")),
                ),
                content=content,
                language=str(turn_data.get("language", "en")),
                created_at=utc_now(),
                updated_at=utc_now(),
            )

            await self.conversation_service.submit_turn(turn)
            existing_turns.add(turn_id)

        existing_documents = {
            document.document_id
            for document in await self.document_service.get_session_documents(
                session_id,
            )
        }

        for document_data, upload in zip(
            documents,
            files,
            strict=True,
        ):
            local_id = str(
                document_data.get("local_id", ""),
            ).strip()

            if not local_id:
                raise ValueError("Document local id is required")

            document_id = self._stable_resource_id(
                "doc",
                draft_id,
                local_id,
            )

            if document_id in existing_documents:
                continue

            document_type = DocumentType(
                str(
                    document_data.get(
                        "document_type",
                        "OTHER",
                    ),
                ),
            )

            filename = upload.filename or str(
                document_data.get(
                    "filename",
                    "document",
                ),
            )

            storage_reference = await self.storage.save(
                session_id,
                upload,
            )

            document = Document(
                document_id=document_id,
                session_id=session_id,
                filename=filename,
                document_type=document_type,
                content_type=(
                    upload.content_type
                    or str(
                        document_data.get(
                            "content_type",
                            "application/octet-stream",
                        ),
                    )
                ),
                size_bytes=(
                    upload.size
                    or int(document_data.get("size_bytes", 0))
                ),
                storage_reference=storage_reference,
                status=DocumentStatus.UPLOADED,
                created_at=utc_now(),
                updated_at=utc_now(),
            )

            try:
                await self.document_service.create_document(
                    document,
                )
            except Exception:
                await self.storage.delete(storage_reference)
                raise

            existing_documents.add(document_id)

        final_session = await self.session_service.get_session(
            session_id,
        )

        if final_session is None:
            raise ValueError(
                "Clinical session could not be loaded after registration",
            )

        patient = await self.patient_service.get_patient(
            final_session.patient_id,
        )

        if patient is None:
            raise ValueError(
                "Patient could not be loaded after registration",
            )

        return final_session, patient, visit_type

    @staticmethod
    def _stable_id(draft_id: str) -> str:
        return hashlib.sha256(
            draft_id.encode(),
        ).hexdigest()[:24]

    @classmethod
    def _stable_resource_id(
        cls,
        prefix: str,
        draft_id: str,
        local_id: str,
    ) -> str:
        return (
            f"{prefix}_"
            f"{cls._stable_id(f'{draft_id}:{local_id}')}"
        )
