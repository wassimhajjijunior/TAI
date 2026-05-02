export default function Loading() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="flex flex-col items-center">
        <div className="animate-spin w-10 h-10 border-4 border-[#004AC6] border-t-transparent rounded-full" />
        <p className="mt-4 text-sm text-[#434655]">Loading...</p>
      </div>
    </div>
  );
}
