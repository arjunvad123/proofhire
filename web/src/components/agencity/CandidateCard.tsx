"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  MapPin,
  ExternalLink,
  Linkedin,
  Github,
  Clock,
  ArrowRight,
} from "lucide-react";
import type { CandidateResponse } from "@/lib/agencity-types";
import type { PipelineStatus } from "@/lib/agencity-types";
import { ScoreBadge } from "./ScoreBadge";
import { TierBadge } from "./TierBadge";
import { UrgencyIndicator } from "./UrgencyIndicator";
import { WarmPathDisplay } from "./WarmPathDisplay";

interface CandidateCardProps {
  candidate: CandidateResponse;
  pipelineStatus?: PipelineStatus;
  compact?: boolean;
  timingSignals?: Array<{ description: string; urgency: "high" | "medium" | "low" }>;
  onStatusChange?: (status: PipelineStatus) => void;
  onViewDetail?: () => void;
  actions?: React.ReactNode;
}

const STATUS_STYLES: Record<PipelineStatus, string> = {
  sourced: "bg-slate-100 text-slate-600",
  contacted: "bg-blue-100 text-blue-700",
  scheduled: "bg-emerald-100 text-emerald-700",
};

export function CandidateCard({
  candidate,
  pipelineStatus,
  compact = false,
  timingSignals,
  onStatusChange,
  onViewDetail,
  actions,
}: CandidateCardProps) {
  const [expanded, setExpanded] = useState(false);

  if (compact) {
    return (
      <div className="bg-white rounded-lg p-4 border border-slate-200 hover:border-emerald-300 hover:shadow-sm transition-all">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-semibold text-slate-900 truncate">
                {candidate.full_name}
              </h4>
              <TierBadge tier={candidate.tier} />
              {pipelineStatus && (
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${STATUS_STYLES[pipelineStatus]}`}>
                  {pipelineStatus}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 truncate mt-0.5">
              {candidate.current_title}
              {candidate.current_company && ` @ ${candidate.current_company}`}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <ScoreBadge score={candidate.combined_score} size="sm" />
            {candidate.timing_urgency !== "low" && (
              <UrgencyIndicator urgency={candidate.timing_urgency} />
            )}
          </div>
        </div>

        {candidate.has_warm_path && (
          <WarmPathDisplay
            connector={candidate.warm_path_connector}
            pathType={candidate.warm_path_type}
            compact
          />
        )}

        {onStatusChange && pipelineStatus && (
          <div className="flex gap-1.5 mt-2">
            {(["sourced", "contacted", "scheduled"] as PipelineStatus[])
              .filter((s) => s !== pipelineStatus)
              .map((s) => (
                <button
                  key={s}
                  onClick={() => onStatusChange(s)}
                  className="px-2 py-1 text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded transition-colors capitalize"
                >
                  Move to {s}
                </button>
              ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden hover:border-emerald-300 hover:shadow-md transition-all">
      {/* Header */}
      <div
        className="p-5 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex justify-between items-start gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h3 className="text-base font-bold text-slate-900">
                {candidate.full_name}
              </h3>
              <TierBadge tier={candidate.tier} />
              {pipelineStatus && (
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${STATUS_STYLES[pipelineStatus]}`}>
                  {pipelineStatus}
                </span>
              )}
            </div>

            <p className="text-sm text-slate-600 mb-2">
              {candidate.current_title}
              {candidate.current_company && (
                <span className="text-slate-400"> @ {candidate.current_company}</span>
              )}
            </p>

            {/* Scores row */}
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <ScoreBadge score={candidate.fit_score} label="Fit" size="sm" />
              <ScoreBadge score={candidate.warmth_score} label="Warmth" size="sm" />
              <ScoreBadge score={candidate.timing_score} label="Timing" size="sm" />
            </div>

            {/* Meta */}
            <div className="flex items-center gap-3 flex-wrap text-xs text-slate-500">
              {candidate.location && (
                <span className="inline-flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5" />
                  {candidate.location}
                </span>
              )}
              {candidate.has_warm_path && (
                <WarmPathDisplay
                  connector={candidate.warm_path_connector}
                  pathType={candidate.warm_path_type}
                  compact
                />
              )}
            </div>

            {/* Timing signals inline */}
            {timingSignals && timingSignals.length > 0 && (
              <div className="flex flex-col gap-1 mt-2">
                {timingSignals.slice(0, 2).map((signal, i) => (
                  <span key={i} className="inline-flex items-center gap-1.5 text-xs">
                    <UrgencyIndicator urgency={signal.urgency} />
                    <span className={signal.urgency === "high" ? "text-red-700" : "text-amber-700"}>
                      {signal.description}
                    </span>
                  </span>
                ))}
              </div>
            )}

            {/* Why consider preview */}
            {candidate.why_consider.length > 0 && (
              <div className="mt-2">
                <p className="text-xs text-slate-500 line-clamp-2">
                  {candidate.why_consider.slice(0, 2).join(" | ")}
                </p>
              </div>
            )}
          </div>

          <div className="flex flex-col items-end gap-2 flex-shrink-0">
            <div className="text-right">
              <span className="text-2xl font-bold text-slate-900">
                {Math.round(candidate.combined_score)}
              </span>
              <span className="text-xs text-slate-400 block">combined</span>
            </div>
            <ChevronDown
              className={`w-5 h-5 text-slate-400 transition-transform ${expanded ? "rotate-180" : ""}`}
            />
          </div>
        </div>
      </div>

      {/* Expanded */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="border-t border-slate-100"
          >
            <div className="p-5 space-y-4">
              {/* Why consider */}
              {candidate.why_consider.length > 0 && (
                <div className="bg-emerald-50 rounded-lg p-4">
                  <p className="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-2">
                    Why Consider
                  </p>
                  <ul className="space-y-1.5">
                    {candidate.why_consider.map((reason, i) => (
                      <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 flex-shrink-0" />
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Timing signals full */}
              {timingSignals && timingSignals.length > 0 && (
                <div className="bg-red-50 rounded-lg p-4">
                  <p className="text-xs font-bold text-red-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    Timing Signals
                  </p>
                  <ul className="space-y-1.5">
                    {timingSignals.map((signal, i) => (
                      <li key={i} className="text-sm flex items-start gap-2">
                        <UrgencyIndicator urgency={signal.urgency} />
                        <span className="text-slate-700">{signal.description}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Warm path */}
              {candidate.has_warm_path && (
                <WarmPathDisplay
                  connector={candidate.warm_path_connector}
                  relationship={candidate.warm_path_relationship}
                  pathType={candidate.warm_path_type}
                  introMessage={candidate.intro_message}
                />
              )}

              {/* Unknowns */}
              {candidate.unknowns.length > 0 && (
                <div className="bg-amber-50 rounded-lg p-4">
                  <p className="text-xs font-bold text-amber-700 uppercase tracking-wider mb-2">
                    Unknowns
                  </p>
                  <ul className="space-y-1.5">
                    {candidate.unknowns.map((item, i) => (
                      <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                        <span className="text-amber-500 font-bold">?</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Research highlights */}
              {candidate.research_highlights.length > 0 && (
                <div className="bg-slate-50 rounded-lg p-4">
                  <p className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
                    Research
                  </p>
                  <ul className="space-y-1.5">
                    {candidate.research_highlights.map((h, i) => (
                      <li key={i} className="text-sm text-slate-700">
                        {h}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Links + Actions */}
              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center gap-3">
                  {candidate.linkedin_url && (
                    <a
                      href={candidate.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 transition-colors"
                    >
                      <Linkedin className="w-4 h-4" />
                      LinkedIn
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                  {candidate.github_url && (
                    <a
                      href={candidate.github_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-800 transition-colors"
                    >
                      <Github className="w-4 h-4" />
                      GitHub
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {actions}
                  {onViewDetail && (
                    <button
                      onClick={onViewDetail}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition-colors"
                    >
                      View Detail
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
