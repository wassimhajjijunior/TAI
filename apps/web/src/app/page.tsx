import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-slate-900">
            P2M-TAI
          </Link>
          <Link href="/dashboard" className="text-sm font-medium text-slate-600 hover:text-slate-900">
            Dashboard
          </Link>
        </div>
      </header>

      <main className="flex min-h-[calc(100vh-73px)] items-center justify-center">
        <div className="text-center max-w-2xl px-6">
          <div className="mb-8">
            <h1 className="text-5xl font-extrabold tracking-tight text-slate-900 mb-4">
              P2M-TAI
            </h1>
            <p className="text-xl text-slate-600 mb-2">
              Procurement AI Platform
            </p>
            <p className="text-slate-500">
              Foundation scaffold ready for Track A and Track B.
            </p>
          </div>
          
          <Link 
            href="/dashboard"
            className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-slate-900 text-white hover:bg-slate-800 h-12 px-8 py-2 transition-colors"
          >
            Go to Dashboard
          </Link>
        </div>
      </main>

      <footer className="border-t bg-white/50">
        <div className="mx-auto max-w-6xl px-6 py-6 text-center text-sm text-slate-500">
          Powered by AI · Demo Mode
        </div>
      </footer>
    </div>
  );
}