"use client";

import { cn } from "@/lib/utils";

interface LoadingStateProps {
  lines?: number;
  className?: string;
}

export function LoadingState({ lines = 3, className }: LoadingStateProps) {
  return (
    <div className={cn("space-y-4 animate-pulse", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="space-y-2">
          <div
            className="h-4 bg-zinc-200 rounded"
            style={{ width: `${80 - i * 15}%` }}
          />
          <div className="h-3 bg-zinc-100 rounded" style={{ width: `${60 - i * 10}%` }} />
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-white rounded-xl p-6 border border-slate-200 animate-pulse">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-zinc-200 rounded-lg" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-zinc-200 rounded w-1/3" />
          <div className="h-3 bg-zinc-100 rounded w-1/2" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-3 bg-zinc-100 rounded w-full" />
        <div className="h-3 bg-zinc-100 rounded w-3/4" />
      </div>
    </div>
  );
}
