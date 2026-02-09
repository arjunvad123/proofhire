"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ExternalLink, Check, AlertTriangle, Clock, Copy } from "lucide-react";

interface ProofBriefModalProps {
  open: boolean;
  onClose: () => void;
}

export function ProofBriefModal({ open, onClose }: ProofBriefModalProps) {
  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (open) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  const handleCopyLink = () => {
    // Simulated
    alert("Share link copied to clipboard!");
  };

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-3xl rounded-2xl border border-zinc-200 bg-white shadow-2xl max-h-[90vh] overflow-y-auto"
          >
            {/* Header */}
            <div className="sticky top-0 bg-white border-b border-zinc-100 px-6 py-4 flex items-center justify-between z-10">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-emerald-100 to-emerald-200 flex items-center justify-center border-2 border-emerald-200">
                  <span className="text-emerald-700 font-semibold">AC</span>
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-bold text-zinc-900">Proof Brief</h2>
                    <span className="text-xs font-medium text-zinc-500 bg-zinc-100 px-2 py-1 rounded">
                      Senior Backend Engineer
                    </span>
                  </div>
                  <p className="text-sm text-zinc-500">Anonymous Candidate · Completed 87 min ago</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyLink}
                  className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100 rounded-lg transition-colors"
                >
                  <Copy className="w-4 h-4" />
                  Share
                </button>
                <button
                  onClick={onClose}
                  className="p-2 text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="p-6">
              {/* Review time badge */}
              <div className="flex items-center gap-2 text-sm text-zinc-500 mb-6">
                <Clock className="w-4 h-4" />
                <span>Typical review time: 5-8 minutes</span>
              </div>

              {/* Proved Claims */}
              <div className="mb-8">
                <h3 className="text-sm font-semibold text-emerald-700 uppercase tracking-wide mb-4 flex items-center gap-2">
                  <Check className="w-4 h-4" />
                  Proved by Code & Evidence
                </h3>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                    <p className="font-semibold text-emerald-900 mb-1">Correctness verified</p>
                    <p className="text-xs text-emerald-700 mb-2">All tests pass, including edge cases for rate limiting</p>
                    <a href="#" className="text-xs text-emerald-600 hover:underline flex items-center gap-1">
                      View test log <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                    <p className="font-semibold text-emerald-900 mb-1">Strong debugging approach</p>
                    <p className="text-xs text-emerald-700 mb-2">Identified off-by-one error, added regression test</p>
                    <a href="#" className="text-xs text-emerald-600 hover:underline flex items-center gap-1">
                      View diff <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                    <p className="font-semibold text-emerald-900 mb-1">Code quality meets bar</p>
                    <p className="text-xs text-emerald-700 mb-2">Clean structure, appropriate abstractions, readable</p>
                    <a href="#" className="text-xs text-emerald-600 hover:underline flex items-center gap-1">
                      View code review <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                    <p className="font-semibold text-amber-900 mb-1">Testing coverage partial</p>
                    <p className="text-xs text-amber-700 mb-2">Core paths covered (78%), some edge cases missing</p>
                    <a href="#" className="text-xs text-amber-600 hover:underline flex items-center gap-1">
                      View coverage <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </div>

              {/* Unproved Claims */}
              <div className="mb-8">
                <h3 className="text-sm font-semibold text-amber-700 uppercase tracking-wide mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Explore in Interview
                </h3>
                <div className="space-y-3">
                  <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <p className="font-semibold text-zinc-900 mb-1">Communication style</p>
                        <p className="text-xs text-zinc-600 mb-3">No writeup provided; unclear how they'd explain tradeoffs</p>
                        <div className="bg-white border border-zinc-200 rounded-lg p-3">
                          <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">Suggested question</p>
                          <p className="text-sm text-zinc-800 italic">
                            "Walk me through your approach to the rate limiter bug. What alternatives did you consider?"
                          </p>
                        </div>
                      </div>
                      <span className="text-xs font-bold text-zinc-500 bg-zinc-200 px-2 py-1 rounded flex-shrink-0">
                        UNPROVED
                      </span>
                    </div>
                  </div>
                  <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <p className="font-semibold text-zinc-900 mb-1">System design thinking</p>
                        <p className="text-xs text-zinc-600 mb-3">Bugfix scope didn't require architectural decisions</p>
                        <div className="bg-white border border-zinc-200 rounded-lg p-3">
                          <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">Suggested question</p>
                          <p className="text-sm text-zinc-800 italic">
                            "How would you scale this rate limiter for 10x traffic? What would break first?"
                          </p>
                        </div>
                      </div>
                      <span className="text-xs font-bold text-zinc-500 bg-zinc-200 px-2 py-1 rounded flex-shrink-0">
                        UNPROVED
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Summary */}
              <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-5">
                <h3 className="text-sm font-semibold text-zinc-900 uppercase tracking-wide mb-4">
                  Summary
                </h3>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <p className="text-xs font-semibold text-zinc-500 uppercase mb-2">Strengths (3 proved)</p>
                    <ul className="space-y-2 text-sm text-zinc-700">
                      <li className="flex items-start gap-2">
                        <Check className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                        <span>Correctness verified with tests</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Check className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                        <span>Strong debugging methodology</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Check className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                        <span>Code quality meets your bar</span>
                      </li>
                    </ul>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-zinc-500 uppercase mb-2">Gaps (2 unproved)</p>
                    <ul className="space-y-2 text-sm text-zinc-700">
                      <li className="flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                        <span>Communication style unclear</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                        <span>System design not demonstrated</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Interview Plan */}
              <div className="mt-6 p-5 bg-blue-50 border border-blue-200 rounded-xl">
                <h3 className="text-sm font-semibold text-blue-900 uppercase tracking-wide mb-3">
                  Suggested 30-minute Interview
                </h3>
                <ol className="space-y-2 text-sm text-blue-800">
                  <li className="flex gap-3">
                    <span className="font-semibold">1.</span>
                    <span>Walk through their debugging approach and alternatives considered</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="font-semibold">2.</span>
                    <span>Ask about edge cases and failure modes they'd monitor in production</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="font-semibold">3.</span>
                    <span>Discuss scaling: what breaks at 10x, how would they redesign?</span>
                  </li>
                </ol>
              </div>

              {/* Footer */}
              <div className="mt-6 pt-4 border-t border-zinc-100 text-center">
                <p className="text-xs text-zinc-400">
                  This is a sample Proof Brief. Actual briefs include links to all artifacts.
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
