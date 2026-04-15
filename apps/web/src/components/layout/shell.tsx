import { Sidebar } from "./sidebar";
import { TopBar } from "./top-bar";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 flex flex-col min-h-screen">
        <TopBar />
        <div className="flex-1 p-10">
          {children}
        </div>
      </main>
    </div>
  );
}
