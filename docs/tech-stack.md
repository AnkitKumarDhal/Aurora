# Stack Table
| Layer | Choice | Why it's here |
| ----- | ------ | ------------- |
| Mobile App | React Native + Expo (Router) | Cross-platform (Android/iOS) from one codebase, fast iteration for a hackathon timeline, built-in file-based navigation |
| Mobile Language | TypeScript | Type safety across screens/API Calls, matches dashboard for shared mental model |
| Voice-to-Text | Whisper API | Converts patient's spoken answers to text for the LLM to process |
| Text-to-Speech | Device/OS Native TTS (`expo-speech`) | Reads AI Questions aloud - no extra API cost/latency, works offline |
| Document OCR | Google Vision API | Extracts text from photographed prescriptions/lab reports |
| Backend Framework | Python + FastAPI | Async-native (pairs with Motor/Mango), auto-generated OpenAPI docs - Useful for both, API Contracts and judges demos |
| Database | MongoDB (via Motor, async driver) | Schema-flexible - good fit since conversation transcripts, extracted docs, and summaries are naturally document-shaped, not relational |
| AI/LLM | LLM API (still to be decided) | Drives adaptive questioning + generates the evidence-linked case summary |
| Web dashboard framework | React + Vite | Fast dev server, standard for a doctor-facing SPA |
| Dashboard Styling | TailwindCSS V4 + shadcn/ui(base-ui) | Fast, consistent, professional looking UI without hand-rolling components under time pressure |
| Dashboard Language | TypeScript | Same reasoning as mobile |
| Auth | Mock auth (MVP) | Real auth (hospital SSO, doctor accounts) is out of scope for hackathon MVP; patients log in via a generated login ID |
| API Docs / Contract | Markdown + FastAPI's auto OpenAPI | One source of truth for all 4 of us |
| Version Control | Git + GitHub | repo: [Aurora](https://github.com/AnkitKumarDhal/Aurora.git) |

# Languages
1. Python (backend)
2. TypeScript/JavaScript (mobile + dashboard)
3. Markdown (.md, for docs)

# Frameworks/Libraries
1. FastAPI
2. Motor
3. Pydantic
4. Expo/Expo Router
5. React Native
6. React
7. Vite
8. Tailwind CSS
9. shadcn/ui
10. React Router

# External APIs/Services
1. LLM API
2. OpenAI Whisper API
3. Google Cloud Vision API,
4. MongoDB (atlas or self-hosted)
