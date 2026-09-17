import { Skeleton } from "@/components/ui/skeleton";

export default function QueueSkeleton() {
  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(268px,1fr))] gap-4">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          className="relative min-h-[140px] overflow-hidden rounded-[14px] border border-border bg-surface p-[18px] pb-4 shadow-[0_10px_24px_-18px_rgba(58,46,92,0.4)]"
          key={index}
        >
          <Skeleton className="absolute inset-x-0 top-0 h-[5px] rounded-none bg-primary-tint" />

          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-28 rounded-md" />
              <Skeleton className="h-3 w-20 rounded-md" />
            </div>

            <Skeleton className="h-5 w-24 rounded-full" />
          </div>

          <div className="mt-5 space-y-2">
            <Skeleton className="h-3 w-full rounded-md" />
            <Skeleton className="h-3 w-4/5 rounded-md" />
          </div>

          <div className="mt-5 flex items-center justify-between">
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-3 w-10 rounded-md" />
          </div>
        </div>
      ))}
    </div>
  );
}
