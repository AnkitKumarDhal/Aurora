# Aurora

**AI-assisted clinical history-taking for Indian OPDs**
Built for Smart India Hackathon — Problem Statement **SIH26047**

> Team: TechTonic

## The problem

In busy Indian OPDs, doctors have only a few minutes per patient, yet a huge portion of that time goes into asking the same structured intake questions — chief complaint, history of present illness, past medical history, allergies, family history — instead of examining and diagnosing. Patients also often forget details, don't bring prior records in a usable form, or struggle to describe symptoms precisely.

## What Aurora does

Aurora is an AI clinical history-taking assistant that a patient interacts with **before** seeing the doctor:

1. **Adaptive conversational interview** — the AI asks one question at a time (by voice or text), and each next question is chosen based on the patient's previous answers, the way a doctor would actually interview a patient — not a static form.
2. **Document understanding** — patients can photograph old prescriptions, lab reports, or discharge summaries; Aurora OCRs and extracts structured data (diagnoses, medications, investigations, dates) from them.
3. **Evidence-linked summary** — Aurora generates a structured case summary (chief complaint, HPI, past history, allergies, family history, review of systems) where **every field is traceable** back to the specific conversation turn or document it came from — so the doctor can trust, verify, and quickly edit it rather than blindly accept AI output.
4. **Doctor dashboard** — a responsive web queue view lets doctors see all waiting patients (red-flagged cases surfaced first), open a full case view, edit the AI's summary, and approve it into the patient's record — usable from a desktop station or a phone browser while moving through the ward.

## Why this approach

Standard digital intake forms don't capture nuance and are a poor fit for patients less comfortable with structured forms. A conversational, adaptive interview mirrors how a real clinical history is actually taken, and evidence-linking is what makes an AI-generated summary something a doctor can actually trust and use in a real clinical workflow, rather than another black-box tool.

## Tech stack

| Layer | Technology |
|---|---|
| Mobile app | React Native + Expo (Expo Router), TypeScript |
| Voice input | Whisper API (speech-to-text) |
| Voice output | Device/OS native TTS (`expo-speech`) |
| Document OCR | Google Cloud Vision API |
| Backend | Python, FastAPI |
| Database | MongoDB (via Motor async driver) |
| AI / LLM | Claude / LLM API (evaluating local Gemma small model as an alternative) |
| Web dashboard | React + Vite, TypeScript |
| Dashboard styling | Tailwind CSS v4 + shadcn/ui (responsive, mobile + desktop) |
| Auth | Mock auth (MVP) — check SIH26047 problem statement for real auth requirements before final submission |

## Project structure
```text
Aurora/
├── backend/                          # FastAPI service
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── routers/                      # auth, sessions, documents, doctor
│   └── services/                     # ocr_service, llm_service, redflag_service
├── mobile/                           # Expo app (patient-facing)
│   └── src/app/                      # register, login, upload, conversation screens
├── dashboard/                        # React + Vite web app (doctor-facing)
│   └── src/pages/                    # LoginPage, QueuePage, PatientDetailPage
└── docs/
    └── API-Contracts.md
```
## Getting started

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Create a `.env` file in `backend/` (never commit this — see `.env.example` for the required keys):
```
MONGO_URI=mongodb://localhost:27017
GOOGLE_VISION_KEY_PATH=path/to/your/service-account.json
```
Run the server:
```bash
uvicorn main:app --reload
```
API will be at `http://localhost:8000`, interactive docs at `http://localhost:8000/docs`.

### Mobile app
```bash
cd mobile
npm install
npm run start
```
Then scan the QR code with Expo Go, or press `a`/`i` for an emulator.

### Dashboard
```bash
cd dashboard
npm install
npm run dev
```
Runs at `http://localhost:5173` by default.

## API contract

The full API contract — every endpoint, request/response shapes, and status codes — lives in [`docs/API-Contracts.md`](docs/API-Contracts.md). This is the single source of truth all three apps (mobile, backend, dashboard) build against. If you change an endpoint's shape, **update this file in the same PR.**

## Contributing

This is a hackathon project with a hard deadline, so speed matters — but so does not breaking each other's work. Follow these rules:

### Branching
- **Never push directly to `main`.** `main` should always be in a working/demoable state.
- Create a branch per feature/fix, off the latest `main`:
```bash
  git checkout main
  git pull origin main
  git checkout -b <type>/<short-description>
```
  Branch name types: `feature/`, `fix/`, `docs/`, `chore/`
  Examples: `feature/adaptive-question-llm`, `fix/auth-login-bug`, `docs/api-contract-update`

### Commits
- Keep commits small and focused — one logical change per commit.
- Write clear messages: `<type>: <what changed>` — e.g. `fix: correct AsyncIOMotorClient typo in db.py`.

### Pull requests
- Open a PR from your branch into `main` as soon as your piece works locally — don't wait until it's "perfect."
- PR description should say **what changed** and **how to test it**.
- At least one other teammate should look over the diff before merging, even a quick skim — we're a team of 4, this takes two minutes and catches a lot.
- Resolve merge conflicts locally (`git pull origin main` into your branch, fix conflicts, push) rather than force-pushing over `main`.
- Delete your branch after merging to keep things tidy.

### Environment variables
- Never commit `.env` files. Keep an up-to-date `.env.example` with variable names (no real values) so anyone cloning the repo knows what to fill in.
- Shared API keys (MongoDB URI, Google Vision key, LLM/Whisper keys) are distributed to the team over a private channel — not through git.

### Before you start work each day
```bash
git checkout main
git pull origin main
git checkout -b your-new-branch
```
Never build on top of an old, out-of-date branch — always branch fresh off `main`.

### Code contract discipline
- If you're changing an API request/response shape, update `docs/API-Contracts.md` in the **same PR** — don't let the doc drift from reality. Everyone else is coding against this file.
- If you hit a blocking bug in someone else's code, fix it in a `fix/` branch and PR it rather than editing on `main` directly — even under time pressure.

### Timeline discipline
- Build deadline: **Wednesday 11:59 PM**
- Thursday: testing + presentation rehearsal
- Friday: submission
- Anything that isn't part of the core loop (register → converse → upload docs → summary → doctor approve) after Monday should go into a "future work" note, not into a rushed PR.
