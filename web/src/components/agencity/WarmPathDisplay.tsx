"use client";

import { useState } from "react";
import { Users, Copy, Check } from "lucide-react";

interface WarmPathDisplayProps {
  connector?: string;
  relationship?: string;
  pathType?: string;
  introMessage?: string;
  compact?: boolean;
}

export function WarmPathDisplay({
  connector,
  relationship,
  pathType,
  introMessage,
  compact = false,
}: WarmPathDisplayProps) {
  const [copied, setCopied] = useState(false);

  async function copyMessage() {
    if (!introMessage) return;
    await navigator.clipboard.writeText(introMessage);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (compact) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-blue-600">
        <Users className="w-3.5 h-3.5" />
        {connector ? `via ${connector}` : pathType || "Warm path available"}
      </span>
    );
  }

  return (
    <div className="bg-blue-50 rounded-lg p-4 space-y-2">
      <div className="flex items-center gap-2">
        <Users className="w-4 h-4 text-blue-600" />
        <span className="text-sm font-medium text-blue-800">
          {connector ? `Connected via ${connector}` : "Warm Introduction"}
        </span>
      </div>

      {relationship && (
        <p className="text-sm text-blue-700">{relationship}</p>
      )}

      {pathType && !relationship && (
        <p className="text-xs text-blue-600 capitalize">
          {pathType.replace(/_/g, " ")}
        </p>
      )}

      {introMessage && (
        <div className="mt-2 bg-white rounded-md p-3 border border-blue-200">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm text-slate-700 whitespace-pre-wrap flex-1">
              {introMessage}
            </p>
            <button
              onClick={copyMessage}
              className="flex-shrink-0 p-1.5 hover:bg-blue-50 rounded transition-colors"
              title="Copy intro message"
            >
              {copied ? (
                <Check className="w-4 h-4 text-emerald-600" />
              ) : (
                <Copy className="w-4 h-4 text-slate-400" />
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
