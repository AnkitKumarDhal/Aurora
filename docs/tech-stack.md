# Aurora — Technology Stack

## Patient Web

- React
- TypeScript
- Vite

## Doctor Web

- React
- TypeScript
- Vite

## Admin Web

- React
- TypeScript
- Vite

## Backend

- Python
- FastAPI
- Pydantic
- Pydantic Settings

## Database

- MongoDB
- PyMongo

## Backend Infrastructure

- HTTPX
- python-multipart
- aiofiles
- PyJWT
- pwdlib
- tenacity
- rapidfuzz

## Testing

- pytest
- pytest-asyncio
- pytest-cov

## AI

AI-related technologies are intentionally not fixed by the core backend.

All AI-related implementation is contained under:

```text
backend/ai/
```

The AI layer may include:

- LLM
- NLP
- OCR
- STT / ASR
- TTS
- clinical conversation processing
- information extraction
- clinical signal extraction
- red-flag detection

The AI implementation team is responsible for selecting and maintaining the dependencies required by these components.

AI-specific dependencies should not be added to the core backend requirements unless the core backend itself directly requires them.

## External Integrations

Initial development uses mock integrations for:

- ABHA
- FHIR
- HIS / EMR

External integration implementations are contained under:

```text
backend/integrations/
```

The core application communicates with integrations through internal interfaces.

## Configuration

Environment-specific configuration is managed through environment variables and `.env` files during local development.

Sensitive credentials must not be committed to the repository.

## Development Environment

The backend targets:

- Python 3.11+
- Node.js
- npm

The frontend applications are independently runnable development servers.

## Architecture Principle

The technology stack is intentionally modular.

The core backend must not depend on a specific AI provider or external healthcare provider.

AI providers and healthcare integrations should be replaceable without restructuring the core application.
