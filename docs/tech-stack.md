# Aurora — Tech Stack

## Frontend

| Application | Stack |
|---|---|
| Patient Web | React, TypeScript, Vite, Tailwind CSS, Framer Motion |
| Doctor Web | React, TypeScript, Vite, Tailwind CSS, React Router |
| Admin Web | React, TypeScript, Vite, Tailwind CSS, Zustand, Framer Motion |

### UI / Frontend Libraries

- **Lucide React** — icons
- **Radix UI / Base UI** — UI primitives
- **Sonner** — doctor-side notifications
- **date-fns** — date/time utilities
- **next-themes** — theme handling

---

## Backend

- **Python**
- **FastAPI** — REST API and dependency injection
- **Pydantic** — request/response validation
- **Pydantic Settings** — configuration management
- **Uvicorn** — ASGI server

---

## Database & Storage

- **MongoDB** — persistent application data
- **PyMongo** — asynchronous MongoDB access
- **Local file storage** — uploaded patient documents

---

## AI

- **Lemonade-compatible OpenAI-style API** — local LLM integration
- **Configurable LLM model** — currently `qwen3.5-9b-FLM`
- **OCR / document extraction** — backend AI processing
- **Browser SpeechRecognition** — patient voice input
- **Browser `getUserMedia()`** — microphone permission/access

AI components are isolated under:

```text
backend/ai/
```

---

## Real-Time

- **Server-Sent Events (SSE)** — live queue, assignment and promotion updates
- **In-process asynchronous event bus** — backend event distribution

---

## Authentication

- **PyJWT** — JWT access tokens
- **pwdlib + Argon2** — password hashing

---

## HTTP / Utilities

- **HTTPX** — asynchronous HTTP client
- **python-multipart** — file uploads
- **aiofiles** — asynchronous file handling
- **tenacity** — retries
- **rapidfuzz** — fuzzy matching

---

## Testing

- **pytest**
- **pytest-asyncio**
- **pytest-cov**

---

## External Integrations

Current development uses mock implementations for:

- ABHA / identity verification
- FHIR
- HIS / EMR

Integration code is isolated under:

```text
backend/integrations/
```
