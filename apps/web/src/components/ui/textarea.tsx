import { forwardRef, type TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <div className="w-full">
        <textarea
          ref={ref}
          className={cn(
            "w-full rounded-xl border bg-[#F2F3FF] px-4 py-3 text-sm text-[#131B2E] placeholder:text-[#737686] resize-none",
            "focus:outline-none focus:ring-2 focus:ring-[#004AC6]",
            error ? "border-[#BA1A1A]" : "border-transparent",
            className
          )}
          {...props}
        />
        {error && <p className="mt-1 text-xs text-[#BA1A1A]">{error}</p>}
      </div>
    );
  }
);
Textarea.displayName = "Textarea";

export { Textarea };
