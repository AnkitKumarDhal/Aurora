export type PatientDraftIdentityMethod = "ABHA" | "AADHAAR";
export type PatientDraftConversationInputType =
  | "AUDIO"
  | "GUIDED_INPUT"
  | "TEXT";
export type PatientDraftDocumentType =
  | "IMAGING_REPORT"
  | "LAB_REPORT"
  | "MEDICAL_RECORD"
  | "OTHER"
  | "PRESCRIPTION";

export interface PatientDraftConversationTurn {
  local_id: string;
  input_type: PatientDraftConversationInputType;
  content: string;
  language: string;
}

export interface PatientDraft {
  version: 1;
  draft_id: string;
  language: "en" | "hi";
  identity_method: PatientDraftIdentityMethod | null;
  identity_identifier: string | null;
  verification_token: string | null;
  consent_version: string | null;
  consent_granted: boolean;
  conversation_turns: PatientDraftConversationTurn[];
  created_at: string;
  updated_at: string;
}

export interface PatientDraftDocument {
  local_id: string;
  draft_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  document_type: PatientDraftDocumentType;
  file: File;
  created_at: string;
}

const DRAFT_STORAGE_KEY = "aurora.patient.draft";
const DOCUMENT_DATABASE_NAME = "aurora-patient-draft";
const DOCUMENT_STORE_NAME = "documents";
const DOCUMENT_DATABASE_VERSION = 1;

function createId(prefix: string): string {
  if (
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
  ) {
    return `${prefix}_${crypto.randomUUID()}`;
  }

  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function getStorage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export function createPatientDraft(language: "en" | "hi"): PatientDraft {
  const timestamp = new Date().toISOString();

  return {
    version: 1,
    draft_id: createId("draft"),
    language,
    identity_method: null,
    identity_identifier: null,
    verification_token: null,
    consent_version: null,
    consent_granted: false,
    conversation_turns: [],
    created_at: timestamp,
    updated_at: timestamp,
  };
}

export function loadPatientDraft(): PatientDraft | null {
  const storage = getStorage();

  if (!storage) {
    return null;
  }

  try {
    const rawDraft = storage.getItem(DRAFT_STORAGE_KEY);

    if (!rawDraft) {
      return null;
    }

    const draft = JSON.parse(rawDraft) as PatientDraft;

    if (
      draft.version !== 1 ||
      typeof draft.draft_id !== "string" ||
      (draft.language !== "en" && draft.language !== "hi") ||
      !Array.isArray(draft.conversation_turns)
    ) {
      return null;
    }

    return draft;
  } catch {
    return null;
  }
}

export function savePatientDraft(draft: PatientDraft): void {
  const storage = getStorage();

  if (!storage) {
    throw new Error("Local patient storage is unavailable.");
  }

  storage.setItem(
    DRAFT_STORAGE_KEY,
    JSON.stringify({
      ...draft,
      updated_at: new Date().toISOString(),
    }),
  );
}

export function clearPatientDraft(): void {
  const storage = getStorage();

  if (!storage) {
    return;
  }

  storage.removeItem(DRAFT_STORAGE_KEY);
}

export function appendPatientDraftConversationTurn(
  draft: PatientDraft,
  turn: Omit<PatientDraftConversationTurn, "local_id">,
): PatientDraft {
  const updatedDraft: PatientDraft = {
    ...draft,
    conversation_turns: [
      ...draft.conversation_turns,
      {
        ...turn,
        local_id: createId("turn"),
      },
    ],
    updated_at: new Date().toISOString(),
  };

  savePatientDraft(updatedDraft);
  return updatedDraft;
}

function openDocumentDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("Local document storage is unavailable."));
      return;
    }

    const request = indexedDB.open(
      DOCUMENT_DATABASE_NAME,
      DOCUMENT_DATABASE_VERSION,
    );

    request.onupgradeneeded = () => {
      const database = request.result;

      if (!database.objectStoreNames.contains(DOCUMENT_STORE_NAME)) {
        const store = database.createObjectStore(DOCUMENT_STORE_NAME, {
          keyPath: "local_id",
        });

        store.createIndex("draft_id", "draft_id", { unique: false });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () =>
      reject(
        request.error ?? new Error("Unable to open local document storage."),
      );
  });
}

function waitForTransaction(transaction: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    transaction.oncomplete = () => resolve();
    transaction.onerror = () =>
      reject(transaction.error ?? new Error("Local document storage failed."));
    transaction.onabort = () =>
      reject(
        transaction.error ?? new Error("Local document storage was aborted."),
      );
  });
}

export async function savePatientDraftDocument(
  draftId: string,
  file: File,
  documentType: PatientDraftDocumentType = "OTHER",
): Promise<PatientDraftDocument> {
  const database = await openDocumentDatabase();

  try {
    const transaction = database.transaction(DOCUMENT_STORE_NAME, "readwrite");

    const document: PatientDraftDocument = {
      local_id: createId("document"),
      draft_id: draftId,
      filename: file.name,
      content_type: file.type || "application/octet-stream",
      size_bytes: file.size,
      document_type: documentType,
      file,
      created_at: new Date().toISOString(),
    };

    transaction.objectStore(DOCUMENT_STORE_NAME).put(document);
    await waitForTransaction(transaction);

    return document;
  } finally {
    database.close();
  }
}

export async function listPatientDraftDocuments(
  draftId: string,
): Promise<PatientDraftDocument[]> {
  const database = await openDocumentDatabase();

  try {
    const transaction = database.transaction(DOCUMENT_STORE_NAME, "readonly");

    const request = transaction
      .objectStore(DOCUMENT_STORE_NAME)
      .index("draft_id")
      .getAll(IDBKeyRange.only(draftId));

    const documents = await new Promise<PatientDraftDocument[]>(
      (resolve, reject) => {
        request.onsuccess = () => {
          const values = request.result as PatientDraftDocument[];

          values.sort((left, right) =>
            left.created_at.localeCompare(right.created_at),
          );

          resolve(values);
        };

        request.onerror = () =>
          reject(request.error ?? new Error("Unable to read local documents."));
      },
    );

    await waitForTransaction(transaction);

    return documents;
  } finally {
    database.close();
  }
}

export async function clearPatientDraftDocuments(
  draftId: string,
): Promise<void> {
  const database = await openDocumentDatabase();

  try {
    const transaction = database.transaction(DOCUMENT_STORE_NAME, "readwrite");

    const request = transaction
      .objectStore(DOCUMENT_STORE_NAME)
      .index("draft_id")
      .openKeyCursor(IDBKeyRange.only(draftId));

    request.onsuccess = () => {
      const cursor = request.result;

      if (!cursor) {
        return;
      }

      cursor.delete();
      cursor.continue();
    };

    await waitForTransaction(transaction);
  } finally {
    database.close();
  }
}

async function clearAllPatientDraftDocuments(): Promise<void> {
  const database = await openDocumentDatabase();

  try {
    const transaction = database.transaction(DOCUMENT_STORE_NAME, "readwrite");

    transaction.objectStore(DOCUMENT_STORE_NAME).clear();

    await waitForTransaction(transaction);
  } finally {
    database.close();
  }
}

export async function clearPatientDraftStorage(
  draftId: string | null,
): Promise<void> {
  clearPatientDraft();

  if (draftId) {
    await clearPatientDraftDocuments(draftId);
    return;
  }

  await clearAllPatientDraftDocuments();
}
