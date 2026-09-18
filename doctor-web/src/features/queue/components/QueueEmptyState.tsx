export default function QueueEmptyState() {
  return (
    <div className="rounded-[20px] border-[1.5px] border-dashed border-border px-5 py-16 text-center">
      <div className="mb-2.5 text-[28px]">🌤️</div>

      <p className="text-[13px] text-text-secondary">
        No patients in this view right now.
      </p>
    </div>
  );
}
