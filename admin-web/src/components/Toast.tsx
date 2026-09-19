import { cn } from "@/lib/utils";
import { useAdminStore } from "@/store/adminStore";

export function Toast() {
  const toast = useAdminStore((state) => state.toast);

  if (!toast) {
    return null;
  }

  return <div className={cn("toast", "show", toast.type)}>{toast.message}</div>;
}
