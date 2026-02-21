"use client";

import { cn } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number;
  label?: string;
  size?: "sm" | "md";
}

function getScoreColor(score: number) {
  if (score >= 80) return "bg-emerald-100 text-emerald-700 ring-emerald-200";
  if (score >= 60) return "bg-blue-100 text-blue-700 ring-blue-200";
  if (score >= 40) return "bg-amber-100 text-amber-700 ring-amber-200";
  return "bg-red-100 text-red-700 ring-red-200";
}

export function ScoreBadge({ score, label, size = "md" }: ScoreBadgeProps) {
  const rounded = Math.round(score);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full ring-1 font-semibold",
        getScoreColor(rounded),
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm"
      )}
    >
      {rounded}
      {label && <span className="font-normal opacity-80">{label}</span>}
    </span>
  );
}
