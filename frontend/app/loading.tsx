export default function Loading() {
  return (
    <div className="min-h-screen bg-[#FFFBF5] p-4 sm:p-6">
      <div className="mx-auto max-w-[1280px] space-y-4">
        <div className="h-16 rounded-2xl bg-stone-100 animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-[1.08fr_0.92fr] gap-5">
          <div className="space-y-4">
            <div className="h-32 rounded-[20px] bg-stone-100 animate-pulse" />
            <div className="h-24 rounded-2xl bg-stone-100 animate-pulse" />
          </div>
          <div className="h-64 rounded-[20px] bg-stone-100 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
