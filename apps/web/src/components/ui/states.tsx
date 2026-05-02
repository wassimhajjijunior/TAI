import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 text-center", className)}>
      {icon && <div className="mb-4 text-[#737686]">{icon}</div>}
      <h3 className="font-headline text-lg font-bold text-[#131B2E] mb-2">{title}</h3>
      {description && <p className="text-sm text-[#434655] mb-4 max-w-sm">{description}</p>}
      {action}
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  message: string;
  retry?: () => void;
}

export function ErrorState({ title = "Something went wrong", message, retry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-12 h-12 rounded-full bg-[#FFDAD6] flex items-center justify-center mb-4">
        <svg className="w-6 h-6 text-[#BA1A1A]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h3 className="font-headline text-lg font-bold text-[#131B2E] mb-2">{title}</h3>
      <p className="text-sm text-[#434655] mb-4 max-w-sm">{message}</p>
      {retry && (
        <button
          onClick={retry}
          className="px-4 py-2 text-sm font-semibold bg-[#EAEDFF] text-[#004AC6] rounded-full hover:bg-[#DAE2FD] transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
