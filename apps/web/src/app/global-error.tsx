"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#FAF8FF] flex items-center justify-center">
        <div className="flex flex-col items-center p-8">
          <div className="w-16 h-16 rounded-full bg-[#FFDAD6] flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-[#BA1A1A]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h1 className="font-headline text-2xl font-bold text-[#131B2E] mb-2">
            Critical Error
          </h1>
          <p className="text-sm text-[#434655] mb-6 text-center max-w-md">
            A critical error occurred. Please refresh the page or contact support if the problem persists.
          </p>
          <button
            onClick={reset}
            className="px-6 py-2.5 bg-gradient-to-r from-[#004AC6] to-[#2563EB] text-white font-bold rounded-full shadow-md"
          >
            Refresh Page
          </button>
        </div>
      </body>
    </html>
  );
}
