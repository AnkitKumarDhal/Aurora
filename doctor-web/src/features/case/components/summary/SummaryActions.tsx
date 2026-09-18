import { Check, LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function SummaryActions({
  isEditing,
  isSaving,
  isConfirming,
  isConfirmed,
  onEdit,
  onSave,
  onCancel,
  onConfirm,
}: {
  isEditing: boolean;
  isSaving: boolean;
  isConfirming: boolean;
  isConfirmed: boolean;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="mt-4.5 flex gap-2 border-t border-border pt-4">
      {isEditing ? (
        <>
          <Button
            className="h-9 rounded-md border border-primary bg-primary-tint px-4 text-xs font-bold text-primary-dark hover:bg-primary-tint"
            disabled={isSaving}
            onClick={onSave}
            type="button"
            variant="outline"
          >
            {isSaving ? (
              <>
                <LoaderCircle className="size-4 animate-spin" />
                Saving
              </>
            ) : (
              "Save changes"
            )}
          </Button>

          <Button
            className="h-9 rounded-md px-4 text-xs font-bold text-text-secondary"
            disabled={isSaving}
            onClick={onCancel}
            type="button"
            variant="ghost"
          >
            Cancel
          </Button>
        </>
      ) : (
        <>
          <Button
            className="h-9 rounded-md border border-border bg-surface-alt px-4 text-xs font-bold text-text-secondary hover:bg-primary-tint hover:text-primary-dark"
            onClick={onEdit}
            type="button"
            variant="outline"
          >
            Edit summary
          </Button>

          <Button
            className="h-9 flex-1 rounded-md bg-primary-dark text-xs font-bold text-surface hover:bg-primary-dark/90"
            disabled={isConfirming || isConfirmed}
            onClick={onConfirm}
            type="button"
          >
            {isConfirming ? (
              <>
                <LoaderCircle className="size-4 animate-spin" />
                Confirming
              </>
            ) : isConfirmed ? (
              <>
                <Check className="size-4" />
                Summary confirmed
              </>
            ) : (
              "Confirm summary"
            )}
          </Button>
        </>
      )}
    </div>
  );
}
