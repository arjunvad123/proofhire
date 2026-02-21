"use client";

import { cn } from "@/lib/utils";

interface TierBadgeProps {
  tier: 1 | 2 | 3;
  label?: string;
}

const TIER_STYLES: Record<1 | 2 | 3, { bg: string; label: string }> = {
  1: { bg: "bg-emerald-100 text-emerald-700", label: "Network" },
  2: { bg: "bg-blue-100 text-blue-700", label: "Warm Intro" },
  3: { bg: "bg-zinc-100 text-zinc-600", label: "Cold" },
};

export function TierBadge({ tier, label }: TierBadgeProps) {
  const style = TIER_STYLES[tier];
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold",
        style.bg
      )}
    >
      {label || style.label}
    </span>
  );
}
