import { useCallback, useState } from "react";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/api/client";
import { confirmSummary, updateSummary } from "@/api/summary";
import type { ClinicalSummary } from "@/types/api";

export interface SummaryForm {
  chief_complaint: string;
  history_of_present_illness: string;
  past_medical_history: string;
  medications: string;
  allergies: string;
}

interface UseSummaryEditorResult {
  form: SummaryForm;
  setForm: React.Dispatch<React.SetStateAction<SummaryForm>>;
  isEditing: boolean;
  isSaving: boolean;
  isConfirming: boolean;
  beginEditing: () => void;
  cancelEditing: () => void;
  saveSummary: () => Promise<void>;
  confirm: () => Promise<void>;
}

const EMPTY_FORM: SummaryForm = {
  chief_complaint: "",
  history_of_present_illness: "",
  past_medical_history: "",
  medications: "",
  allergies: "",
};

function summaryToForm(summary: ClinicalSummary): SummaryForm {
  return {
    chief_complaint: summary.chief_complaint ?? "",
    history_of_present_illness: summary.history_of_present_illness ?? "",
    past_medical_history: summary.past_medical_history.join(", "),
    medications: summary.medications.join(", "),
    allergies: summary.allergies.join(", "),
  };
}

function parseList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function useSummaryEditor(
  sessionId: string | undefined,
  summary: ClinicalSummary | null,
  refresh: () => Promise<void>,
): UseSummaryEditorResult {
  const [form, setForm] = useState<SummaryForm>(() =>
    summary ? summaryToForm(summary) : EMPTY_FORM,
  );
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  const beginEditing = useCallback((): void => {
    if (!summary) {
      return;
    }

    setForm(summaryToForm(summary));
    setIsEditing(true);
  }, [summary]);

  const cancelEditing = useCallback((): void => {
    setIsEditing(false);
    setForm(summary ? summaryToForm(summary) : EMPTY_FORM);
  }, [summary]);

  const saveSummary = useCallback(async (): Promise<void> => {
    if (!sessionId) {
      return;
    }

    setIsSaving(true);

    try {
      await updateSummary(sessionId, {
        chief_complaint: form.chief_complaint.trim() || null,
        history_of_present_illness:
          form.history_of_present_illness.trim() || null,
        past_medical_history: parseList(form.past_medical_history),
        medications: parseList(form.medications),
        allergies: parseList(form.allergies),
      });

      setIsEditing(false);
      await refresh();
      toast.success("Summary saved");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to save summary."));
    } finally {
      setIsSaving(false);
    }
  }, [form, refresh, sessionId]);

  const confirm = useCallback(async (): Promise<void> => {
    if (!sessionId) {
      return;
    }

    setIsConfirming(true);

    try {
      await confirmSummary(sessionId);
      await refresh();
      toast.success("Summary confirmed");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to confirm summary."));
    } finally {
      setIsConfirming(false);
    }
  }, [refresh, sessionId]);

  return {
    form,
    setForm,
    isEditing,
    isSaving,
    isConfirming,
    beginEditing,
    cancelEditing,
    saveSummary,
    confirm,
  };
}
