"use client";

import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  icon: LucideIcon;
  value: number | string;
  label: string;
  trend?: string;
  iconBg?: string;
  iconColor?: string;
  className?: string;
}

export function StatsCard({
  icon: Icon,
  value,
  label,
  trend,
  iconBg = "bg-emerald-100",
  iconColor = "text-emerald-600",
  className,
}: StatsCardProps) {
  return (
    <div
      className={cn(
        "bg-white rounded-xl p-6 border border-slate-200 shadow-sm",
        className
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", iconBg)}>
          <Icon className={cn("w-5 h-5", iconColor)} />
        </div>
        <span className="text-2xl font-bold text-slate-900">
          {typeof value === "number" ? value.toLocaleString() : value}
        </span>
      </div>
      <h3 className="text-sm font-medium text-slate-600">{label}</h3>
      {trend && <p className="text-xs text-slate-500 mt-0.5">{trend}</p>}
    </div>
  );
}
