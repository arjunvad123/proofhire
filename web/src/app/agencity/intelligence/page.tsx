"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  TrendingUp,
  AlertCircle,
  Clock,
  Briefcase,
  Building2,
  Zap,
  CalendarDays,
  Users
} from "lucide-react";
import { motion } from "framer-motion";

export default function IntelligencePage() {
  const searchParams = useSearchParams();
  const companyId = searchParams.get("company");

  // Demo timing intelligence data for Confido
  const timingData = companyId === "100b5ac1-1912-4970-a378-04d0169fd597" ? {
    high_urgency: [
      {
        name: "Mike Johnson",
        title: "Senior Engineer",
        company: "Stripe",
        signal: "Company announced layoffs affecting his department",
        readiness_score: 95,
        days_ago: 5,
      },
      {
        name: "Sarah Chen",
        title: "Staff Engineer",
        company: "Meta",
        signal: "Role elimination announced",
        readiness_score: 92,
        days_ago: 12,
      },
    ],
    medium_urgency: [
      {
        name: "Lisa Park",
        title: "Backend Engineer",
        company: "Google",
        signal: "4+ years at current role, updated LinkedIn recently",
        readiness_score: 72,
        days_ago: 30,
      },
      {
        name: "James Wilson",
        title: "Engineering Manager",
        company: "Amazon",
        signal: "Long tenure, actively engaging with posts",
        readiness_score: 68,
        days_ago: 45,
      },
    ],
  } : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href={`/agencity/dashboard?company=${companyId}`}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-slate-600" />
              </Link>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Timing Intelligence</h1>
                <p className="text-sm text-slate-500">Find people ready to make a move</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-purple-500" />
              <span className="text-sm font-medium text-slate-600">Network Analysis</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl p-6 border border-red-200 shadow-sm"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900">
                  {timingData?.high_urgency.length || 0}
                </div>
                <div className="text-xs text-slate-600">High Urgency</div>
              </div>
            </div>
            <p className="text-xs text-slate-500">Act within 1 week</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl p-6 border border-amber-200 shadow-sm"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                <Clock className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900">
                  {timingData?.medium_urgency.length || 0}
                </div>
                <div className="text-xs text-slate-600">Medium Urgency</div>
              </div>
            </div>
            <p className="text-xs text-slate-500">Act within 1 month</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900">
                  {companyId === "100b5ac1-1912-4970-a378-04d0169fd597" ? "3,637" : "0"}
                </div>
                <div className="text-xs text-slate-600">Total Network</div>
              </div>
            </div>
            <p className="text-xs text-slate-500">Analyzed connections</p>
          </motion.div>
        </div>

        {/* High Urgency Candidates */}
        {timingData && timingData.high_urgency.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <h2 className="text-lg font-bold text-slate-900">High Urgency</h2>
              <span className="text-sm text-slate-500">(Act within 1 week)</span>
            </div>

            <div className="space-y-4">
              {timingData.high_urgency.map((candidate, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white rounded-xl p-6 border-l-4 border-red-500 shadow-sm"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-1">
                        {candidate.name}
                      </h3>
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Briefcase className="w-4 h-4" />
                        <span>{candidate.title} @ {candidate.company}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-red-600">
                        {candidate.readiness_score}
                      </div>
                      <div className="text-xs text-slate-500">Readiness</div>
                    </div>
                  </div>

                  <div className="bg-red-50 rounded-lg p-3 mb-3">
                    <div className="flex items-start gap-2">
                      <Zap className="w-4 h-4 text-red-600 mt-0.5" />
                      <div>
                        <div className="text-sm font-medium text-red-900 mb-1">Signal</div>
                        <div className="text-sm text-red-800">{candidate.signal}</div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <CalendarDays className="w-3 h-3" />
                      <span>{candidate.days_ago} days ago</span>
                    </div>
                    <button className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-medium rounded-lg transition-colors">
                      Reach Out Now
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Medium Urgency Candidates */}
        {timingData && timingData.medium_urgency.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Clock className="w-5 h-5 text-amber-500" />
              <h2 className="text-lg font-bold text-slate-900">Medium Urgency</h2>
              <span className="text-sm text-slate-500">(Act within 1 month)</span>
            </div>

            <div className="space-y-4">
              {timingData.medium_urgency.map((candidate, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 + 0.2 }}
                  className="bg-white rounded-xl p-6 border-l-4 border-amber-500 shadow-sm"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-1">
                        {candidate.name}
                      </h3>
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Briefcase className="w-4 h-4" />
                        <span>{candidate.title} @ {candidate.company}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-amber-600">
                        {candidate.readiness_score}
                      </div>
                      <div className="text-xs text-slate-500">Readiness</div>
                    </div>
                  </div>

                  <div className="bg-amber-50 rounded-lg p-3 mb-3">
                    <div className="flex items-start gap-2">
                      <TrendingUp className="w-4 h-4 text-amber-600 mt-0.5" />
                      <div>
                        <div className="text-sm font-medium text-amber-900 mb-1">Signal</div>
                        <div className="text-sm text-amber-800">{candidate.signal}</div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <CalendarDays className="w-3 h-3" />
                      <span>{candidate.days_ago} days ago</span>
                    </div>
                    <button className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium rounded-lg transition-colors">
                      Schedule Outreach
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* No Data State */}
        {!timingData && (
          <div className="text-center py-16">
            <TrendingUp className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">
              No Timing Intelligence Yet
            </h3>
            <p className="text-slate-600 mb-6">
              Import your LinkedIn connections to see timing insights
            </p>
            <Link
              href={`/agencity/dashboard?company=${companyId}`}
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors"
            >
              Go to Dashboard
            </Link>
          </div>
        )}

        {/* Info Box */}
        {timingData && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <Zap className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-blue-900 mb-2">
                  How Timing Intelligence Works
                </h3>
                <div className="space-y-2 text-sm text-blue-800">
                  <p>
                    <strong>High Urgency:</strong> People affected by layoffs, role changes, or showing active job-seeking signals. Reach out within 1 week.
                  </p>
                  <p>
                    <strong>Medium Urgency:</strong> People with long tenure (3+ years), recent profile updates, or career milestones. Good time to reconnect.
                  </p>
                  <p className="text-xs text-blue-700 mt-3">
                    💡 <strong>Tip:</strong> Timing is everything in recruiting. A warm outreach at the right moment converts 10x better than cold outreach.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
