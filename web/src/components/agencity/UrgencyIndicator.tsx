"use client";

import { cn } from "@/lib/utils";

interface UrgencyIndicatorProps {
  urgency: "high" | "medium" | "low";
  label?: string;
}

const URGENCY_STYLES = {
  high: "bg-red-500 animate-pulse",
  medium: "bg-amber-500",
  low: "bg-zinc-400",
};

const URGENCY_TEXT = {
  high: "text-red-700",
  medium: "text-amber-700",
  low: "text-zinc-500",
};

export function UrgencyIndicator({ urgency, label }: UrgencyIndicatorProps) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={cn("w-2 h-2 rounded-full", URGENCY_STYLES[urgency])} />
      {label && (
        <span className={cn("text-xs font-medium", URGENCY_TEXT[urgency])}>
          {label}
        </span>
      )}
    </span>
  );
}
