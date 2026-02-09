"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Settings, Code, FileCheck, ChevronDown } from "lucide-react";

interface Step {
  number: string;
  title: string;
  description: string;
  detail: string;
  icon: React.ReactNode;
  visual: React.ReactNode;
}

export function HowItWorks() {
  const [activeStep, setActiveStep] = useState(0);
  const [expandedMobile, setExpandedMobile] = useState<number | null>(0);

  const steps: Step[] = [
    {
      number: "01",
      title: "Calibrate your bar",
      description: "15-minute founder interview",
      detail: "A short calibration creates your Company Operating Model: pace, quality bar, autonomy, and what 'good' means at your startup. No generic rubrics.",
      icon: <Settings className="w-6 h-6" />,
      visual: (
        <div className="space-y-4">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center mx-auto mb-4">
              <Settings className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Company Operating Model</h3>
            <p className="text-gray-400 text-sm">Your calibration defines the rubric</p>
          </div>
          <div className="space-y-3 max-w-xs mx-auto">
            <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-400 text-xs">Pace</span>
                <span className="text-white text-xs font-medium">High</span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full w-4/5 bg-blue-500 rounded-full" />
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-400 text-xs">Quality bar</span>
                <span className="text-white text-xs font-medium">High</span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full w-[90%] bg-emerald-500 rounded-full" />
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-400 text-xs">Autonomy expected</span>
                <span className="text-white text-xs font-medium">Medium</span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full w-3/5 bg-amber-500 rounded-full" />
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      number: "02",
      title: "Candidate completes real work",
      description: "60-90 minute work sample",
      detail: "Bugfix, feature slice, or refactor in a secure sandbox. We capture diffs, test logs, coverage, and writeups—automatically. AI tools configurable by company.",
      icon: <Code className="w-6 h-6" />,
      visual: (
        <div className="space-y-4">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center mx-auto mb-4">
              <Code className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Secure Sandbox</h3>
            <p className="text-gray-400 text-sm">Real work, captured artifacts</p>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden max-w-sm mx-auto">
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-900 border-b border-gray-700">
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <div className="w-2 h-2 rounded-full bg-yellow-500" />
                <div className="w-2 h-2 rounded-full bg-green-500" />
              </div>
              <span className="text-gray-500 text-xs">rate_limiter.py</span>
            </div>
            <div className="p-4 font-mono text-xs">
              <div className="text-gray-500">1  def check_rate_limit(user_id):</div>
              <div className="text-red-400 bg-red-500/10">2-     if count &gt; limit:</div>
              <div className="text-emerald-400 bg-emerald-500/10">2+     if count &gt;= limit:</div>
              <div className="text-gray-500">3      return RateLimitError()</div>
            </div>
          </div>
          <div className="flex justify-center gap-2">
            <span className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-400">diff.patch</span>
            <span className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-400">test.log</span>
            <span className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-400">coverage.xml</span>
          </div>
        </div>
      ),
    },
    {
      number: "03",
      title: "Review the Proof Brief",
      description: "5-8 minutes to decide",
      detail: "A shareable 1-page decision packet: PROVED vs UNPROVED claims, evidence links, and a focused interview plan. Forward it to your co-founder.",
      icon: <FileCheck className="w-6 h-6" />,
      visual: (
        <div className="space-y-4">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center mx-auto mb-4">
              <FileCheck className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Proof Brief</h3>
            <p className="text-gray-400 text-sm">Evidence-backed decision packet</p>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 max-w-sm mx-auto">
            <div className="space-y-2">
              <div className="flex items-center justify-between p-2 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                <span className="text-emerald-400 text-sm">Correctness</span>
                <span className="text-[10px] font-bold text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded">PROVED</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                <span className="text-emerald-400 text-sm">Code Quality</span>
                <span className="text-[10px] font-bold text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded">PROVED</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <span className="text-amber-400 text-sm">Testing</span>
                <span className="text-[10px] font-bold text-amber-300 bg-amber-500/20 px-2 py-0.5 rounded">PARTIAL</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-gray-700/50 border border-gray-600 rounded-lg">
                <span className="text-gray-400 text-sm">Communication</span>
                <span className="text-[10px] font-bold text-gray-400 bg-gray-600 px-2 py-0.5 rounded">UNPROVED</span>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-gray-700">
              <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-1">Interview prompt</p>
              <p className="text-xs text-gray-300">"Walk through your edge case handling..."</p>
            </div>
          </div>
        </div>
      ),
    },
  ];

  return (
    <section id="how-it-works" className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
            How it works
          </h2>
          <p className="text-lg text-zinc-600 max-w-2xl mx-auto">
            From calibration to decision in three steps.
          </p>
        </div>

        {/* Desktop: Side by side */}
        <div className="hidden lg:grid lg:grid-cols-2 gap-16 items-start">
          {/* Left: Steps */}
          <div className="space-y-2">
            {steps.map((step, index) => (
              <button
                key={index}
                onClick={() => setActiveStep(index)}
                className={`w-full text-left px-6 py-5 rounded-xl transition-all duration-300 ${
                  activeStep === index
                    ? "bg-white shadow-lg border border-zinc-200"
                    : "hover:bg-zinc-50"
                }`}
              >
                <div className="flex items-center gap-4">
                  <span className={`text-sm font-medium transition-colors ${
                    activeStep === index ? "text-emerald-600" : "text-zinc-400"
                  }`}>
                    {step.number}
                  </span>
                  <div>
                    <span className={`text-lg font-medium transition-colors ${
                      activeStep === index ? "text-zinc-900" : "text-zinc-600"
                    }`}>
                      {step.title}
                    </span>
                    <span className={`block text-sm ${
                      activeStep === index ? "text-zinc-500" : "text-zinc-400"
                    }`}>
                      {step.description}
                    </span>
                  </div>
                </div>
                <AnimatePresence>
                  {activeStep === index && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <p className="text-zinc-600 text-sm mt-4 pl-10">
                        {step.detail}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </button>
            ))}
          </div>

          {/* Right: Visual */}
          <div className="sticky top-24">
            <div className="rounded-2xl bg-[#1a1a1a] border border-gray-800 overflow-hidden shadow-2xl">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
              </div>
              <div className="p-8 min-h-[400px] flex items-center justify-center">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeStep}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                    className="w-full"
                  >
                    {steps[activeStep].visual}
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile: Accordion */}
        <div className="lg:hidden space-y-4">
          {steps.map((step, index) => (
            <div
              key={index}
              className="rounded-xl border border-zinc-200 overflow-hidden bg-white"
            >
              <button
                onClick={() => setExpandedMobile(expandedMobile === index ? null : index)}
                className="w-full text-left px-5 py-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-emerald-600">{step.number}</span>
                  <div>
                    <span className="font-medium text-zinc-900">{step.title}</span>
                    <span className="block text-sm text-zinc-500">{step.description}</span>
                  </div>
                </div>
                <ChevronDown className={`w-5 h-5 text-zinc-400 transition-transform ${
                  expandedMobile === index ? "rotate-180" : ""
                }`} />
              </button>
              <AnimatePresence>
                {expandedMobile === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="px-5 pb-5">
                      <p className="text-zinc-600 text-sm mb-4">{step.detail}</p>
                      <div className="rounded-xl bg-[#1a1a1a] border border-gray-800 p-6">
                        {step.visual}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
