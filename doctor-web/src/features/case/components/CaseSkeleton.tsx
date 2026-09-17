import { Skeleton } from "@/components/ui/skeleton";

export default function CaseSkeleton() {
  return (
    <div className="space-y-5">
      <div className="rounded-[20px] border border-border bg-surface px-6 py-[22px]">
        <div className="flex items-center justify-between gap-5">
          <div className="flex items-center gap-3.5">
            <Skeleton className="size-[52px] rounded-2xl" />

            <div className="space-y-2">
              <Skeleton className="h-5 w-32 rounded-md" />

              <div className="flex gap-2">
                <Skeleton className="h-3 w-12 rounded-md" />
                <Skeleton className="h-4 w-24 rounded-full" />
                <Skeleton className="h-3 w-16 rounded-md" />
              </div>
            </div>
          </div>

          <Skeleton className="h-9 w-28 rounded-md" />
        </div>

        <div className="mt-5 flex gap-3">
          <Skeleton className="size-[22px] rounded-full" />
          <Skeleton className="h-3 w-16 rounded-md" />
          <Skeleton className="h-0.5 w-7 rounded-full" />
          <Skeleton className="size-[22px] rounded-full" />
          <Skeleton className="h-3 w-12 rounded-md" />
          <Skeleton className="h-0.5 w-7 rounded-full" />
          <Skeleton className="size-[22px] rounded-full" />
          <Skeleton className="h-3 w-24 rounded-md" />
        </div>
      </div>

      <div className="grid items-start gap-5 lg:grid-cols-[1.6fr_1fr]">
        <div className="space-y-4">
          <div className="rounded-[20px] border border-border bg-surface px-[22px] py-5">
            <div className="mb-5 flex items-center justify-between">
              <Skeleton className="h-4 w-32 rounded-md" />
              <Skeleton className="h-5 w-20 rounded-full" />
            </div>

            <div className="space-y-5">
              <div className="space-y-2">
                <Skeleton className="h-3 w-24 rounded-md" />
                <Skeleton className="h-4 w-64 rounded-md" />
              </div>

              <div className="space-y-2">
                <Skeleton className="h-3 w-40 rounded-md" />
                <Skeleton className="h-4 w-full rounded-md" />
                <Skeleton className="h-4 w-4/5 rounded-md" />
              </div>

              <div className="space-y-2">
                <Skeleton className="h-3 w-32 rounded-md" />
                <Skeleton className="h-6 w-28 rounded-full" />
              </div>

              <div className="space-y-2">
                <Skeleton className="h-3 w-24 rounded-md" />
                <Skeleton className="h-6 w-36 rounded-full" />
              </div>
            </div>
          </div>

          <div className="rounded-[20px] border border-border bg-surface px-[22px] py-5">
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-20 rounded-md" />
              <Skeleton className="h-3 w-10 rounded-md" />
            </div>

            <div className="mt-4 space-y-2">
              <Skeleton className="h-11 w-full rounded-md" />
              <Skeleton className="h-11 w-full rounded-md" />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-[20px] border border-border bg-surface px-[22px] py-5">
            <Skeleton className="mb-5 h-4 w-16 rounded-md" />

            <div className="space-y-4">
              <Skeleton className="h-8 w-full rounded-md" />
              <Skeleton className="h-8 w-full rounded-md" />
              <Skeleton className="h-8 w-full rounded-md" />
              <Skeleton className="h-8 w-full rounded-md" />
            </div>
          </div>

          <div className="rounded-[20px] border border-border bg-surface px-[22px] py-5">
            <Skeleton className="mb-5 h-4 w-28 rounded-md" />

            <div className="space-y-4">
              <Skeleton className="h-6 w-full rounded-md" />
              <Skeleton className="h-6 w-full rounded-md" />
              <Skeleton className="h-6 w-full rounded-md" />
              <Skeleton className="h-6 w-full rounded-md" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
