"use client";

import { useState } from "react";
import { X, Copy, Check, Loader2, Sparkles } from "lucide-react";
import { generateIntroRequests } from "@/lib/agencity-api";

interface GenerateIntroDialogProps {
  open: boolean;
  onClose: () => void;
  candidateName: string;
  candidateId: string;
  roleTitle: string;
  requiredSkills?: string[];
}

export function GenerateIntroDialog({
  open,
  onClose,
  candidateName,
  candidateId,
  roleTitle,
  requiredSkills,
}: GenerateIntroDialogProps) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [connector, setConnector] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function generate() {
    setLoading(true);
    setError(null);
    const result = await generateIntroRequests({
      role_title: roleTitle,
      required_skills: requiredSkills,
      target_person_ids: [candidateId],
      limit: 1,
    });
    setLoading(false);

    if (result.error) {
      setError(result.error);
      return;
    }

    if (result.data && result.data.requests.length > 0) {
      const req = result.data.requests[0];
      setMessage(req.message);
      setConnector(req.connector_name);
    } else {
      setError("No intro path found for this candidate.");
    }
  }

  async function copyMessage() {
    if (!message) return;
    await navigator.clipboard.writeText(message);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 z-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-slate-900">
            Generate Intro to {candidateName}
          </h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        <p className="text-sm text-slate-500 mb-4">
          For: <span className="font-medium text-slate-700">{roleTitle}</span>
        </p>

        {!message && !loading && (
          <button
            onClick={generate}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            Generate Intro Message
          </button>
        )}

        {loading && (
          <div className="flex items-center justify-center gap-2 py-8 text-slate-500">
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating personalized intro...
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">
            {error}
          </div>
        )}

        {message && (
          <div className="space-y-3">
            {connector && (
              <p className="text-sm text-blue-700 bg-blue-50 px-3 py-2 rounded-lg">
                Reach out via: <span className="font-medium">{connector}</span>
              </p>
            )}
            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
              <p className="text-sm text-slate-700 whitespace-pre-wrap">
                {message}
              </p>
            </div>
            <button
              onClick={copyMessage}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-emerald-600" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy Message
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
