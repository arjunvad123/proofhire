"use client";

import { useState } from "react";
import { useScroll, useTransform, motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { HowItWorks } from "./HowItWorks";
import { FAQ } from "./FAQ";
import { UniversityCarousel } from "./UniversityCarousel";
import { ProofBriefModal } from "./ProofBriefModal";
import { Check, Shield, FileCheck, Clock, ArrowRight, X, Cpu, Target, Zap, Search, BarChart3 } from "lucide-react";

export function AgencityLandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showProofBriefModal, setShowProofBriefModal] = useState(false);
  const [email, setEmail] = useState("");
  const [userType, setUserType] = useState<"founder" | "candidate">("founder");

  // Header Scroll Effects
  const { scrollY } = useScroll();
  const headerOpacity = useTransform(scrollY, [0, 200], [1, 0.95]);
  const headerScale = useTransform(scrollY, [0, 200], [1, 0.98]);

  const currentYear = new Date().getFullYear();

  const handleGetStarted = () => {
    document.getElementById("waitlist")?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSubmitWaitlist = (e: React.FormEvent) => {
    e.preventDefault();
    alert(`Thanks! We'll be in touch at ${email}`);
    setEmail("");
  };

  return (
    <div className="min-h-screen bg-white font-sans text-zinc-900 selection:bg-indigo-100 selection:text-indigo-900">
      {/* Floating Header */}
      <motion.header
        className="fixed top-6 left-0 right-0 z-50 flex justify-center px-4 pointer-events-none"
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <motion.div
          className="pointer-events-auto w-full max-w-3xl bg-[#121212]/70 backdrop-blur-2xl border border-white/10 rounded-full px-5 py-3 flex items-center justify-between shadow-2xl transition-all duration-300 relative overflow-hidden"
          style={{
            boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
            opacity: headerOpacity,
            scale: headerScale,
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent pointer-events-none skew-x-12" />

          <Link href="/" className="flex items-center gap-3 pl-2 transition-opacity hover:opacity-80 relative z-10">
            <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
              <Cpu className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold text-white tracking-tight">Agencity</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6 relative z-10">
            <a href="#company-model" className="text-sm font-medium text-white/70 hover:text-white transition-colors">Company Model</a>
            <a href="#how-it-works" className="text-sm font-medium text-white/70 hover:text-white transition-colors">How it works</a>
            <a href="#trust" className="text-sm font-medium text-white/70 hover:text-white transition-colors">Trust</a>
            <a href="#faq" className="text-sm font-medium text-white/70 hover:text-white transition-colors">FAQ</a>
          </nav>

          <div className="flex items-center gap-3 pr-1 relative z-10">
            <Button
              onClick={handleGetStarted}
              className="rounded-full px-5 sm:px-6 py-1.5 sm:py-2 text-xs sm:text-sm font-semibold text-black bg-white hover:bg-gray-100 transition-all duration-300 transform hover:scale-105"
            >
              Request Access
            </Button>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-white hover:bg-white/10 rounded-full transition-colors relative z-10"
              aria-label="Toggle menu"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </motion.div>

        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="pointer-events-auto absolute top-[80px] w-[90%] max-w-md bg-[#000000]/90 backdrop-blur-3xl border border-white/10 rounded-2xl shadow-2xl p-4 md:hidden z-50"
            >
              <div className="space-y-1 relative z-10">
                <a href="#company-model" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-3 text-base font-medium text-white/80 hover:bg-white/10 hover:text-white rounded-xl transition-colors">Company Model</a>
                <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-3 text-base font-medium text-white/80 hover:bg-white/10 hover:text-white rounded-xl transition-colors">How it works</a>
                <a href="#trust" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-3 text-base font-medium text-white/80 hover:bg-white/10 hover:text-white rounded-xl transition-colors">Trust</a>
                <a href="#faq" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-3 text-base font-medium text-white/80 hover:bg-white/10 hover:text-white rounded-xl transition-colors">FAQ</a>
                <div className="border-t border-white/10 my-3"></div>
                <button onClick={() => { handleGetStarted(); setMobileMenuOpen(false); }} className="w-full px-4 py-4 mt-2 text-base font-bold text-black bg-white hover:bg-gray-100 rounded-xl transition-all shadow-lg">
                  Request Access
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.header>

      {/* Hero Section - Company Model Focus */}
      <section className="relative pt-32 pb-16 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-slate-50 via-white to-white z-0" />

        <div className="relative z-10 mx-auto max-w-6xl px-4">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            {/* Left: Copy */}
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-medium mb-6">
                <Cpu className="w-4 h-4" />
                Your Company Model for Hiring
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-semibold leading-tight tracking-tight text-zinc-900">
                Make your hiring bar{" "}
                <span className="text-emerald-600">executable.</span>
              </h1>

              <p className="mt-6 max-w-xl text-lg leading-relaxed text-zinc-600 md:text-xl">
                Agencity builds a company-specific evaluation model that generates role-relevant benchmarks and produces Proof Briefs—what's proven, what isn't, and what to verify next.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <button
                  onClick={handleGetStarted}
                  className="inline-flex items-center justify-center rounded-xl bg-zinc-900 px-6 py-3.5 text-sm font-semibold text-white hover:bg-zinc-800 transition-colors shadow-lg shadow-zinc-900/10"
                >
                  Build your Company Model
                  <ArrowRight className="ml-2 w-4 h-4" />
                </button>
                <button
                  onClick={() => setShowProofBriefModal(true)}
                  className="inline-flex items-center justify-center rounded-xl border border-zinc-200 bg-white px-6 py-3.5 text-sm font-semibold text-zinc-900 hover:bg-zinc-50 hover:border-zinc-300 transition-colors"
                >
                  See sample output
                </button>
              </div>

              <div className="mt-8 flex items-center gap-6 text-sm text-zinc-500">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-emerald-600" />
                  <span>Your bar, executable</span>
                </div>
                <div className="flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-emerald-600" />
                  <span>Evidence-bound</span>
                </div>
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-emerald-600" />
                  <span>Gap analysis</span>
                </div>
              </div>
            </div>

            {/* Right: Company Model → Proof Brief Visual */}
            <div className="relative">
              <div className="absolute -inset-4 rounded-3xl bg-gradient-to-r from-emerald-500/10 via-blue-400/10 to-purple-500/10 blur-2xl" />

              {/* Company Model Visual */}
              <div className="relative space-y-4">
                {/* Company Model Panel */}
                <div className="rounded-2xl border border-zinc-200 bg-white shadow-lg overflow-hidden">
                  <div className="flex items-center gap-2 px-4 py-2.5 bg-zinc-900 border-b border-zinc-700">
                    <Cpu className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm font-medium text-white">Company Model</span>
                    <span className="ml-auto text-xs text-zinc-400">Your hiring bar</span>
                  </div>
                  <div className="p-4 space-y-3">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-zinc-600">Quality Bar</span>
                        <span className="font-medium text-zinc-900">High</span>
                      </div>
                      <div className="h-2 bg-zinc-100 rounded-full overflow-hidden">
                        <div className="h-full w-[85%] bg-emerald-500 rounded-full" />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-zinc-600">Pace</span>
                        <span className="font-medium text-zinc-900">Fast</span>
                      </div>
                      <div className="h-2 bg-zinc-100 rounded-full overflow-hidden">
                        <div className="h-full w-[75%] bg-blue-500 rounded-full" />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-zinc-600">Autonomy</span>
                        <span className="font-medium text-zinc-900">High</span>
                      </div>
                      <div className="h-2 bg-zinc-100 rounded-full overflow-hidden">
                        <div className="h-full w-[80%] bg-purple-500 rounded-full" />
                      </div>
                    </div>
                    <div className="pt-2 border-t border-zinc-100">
                      <p className="text-xs text-zinc-500">Benchmarks generated:</p>
                      <div className="flex gap-2 mt-1">
                        <span className="px-2 py-0.5 bg-zinc-100 rounded text-xs">bugfix_v3</span>
                        <span className="px-2 py-0.5 bg-zinc-100 rounded text-xs">feature_slice</span>
                        <span className="px-2 py-0.5 bg-zinc-100 rounded text-xs">refactor</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Arrow */}
                <div className="flex justify-center">
                  <div className="w-8 h-8 rounded-full bg-zinc-100 flex items-center justify-center">
                    <ArrowRight className="w-4 h-4 text-zinc-400 rotate-90" />
                  </div>
                </div>

                {/* Proof Brief Output */}
                <div
                  className="rounded-2xl border border-zinc-200 bg-white shadow-lg overflow-hidden cursor-pointer hover:shadow-xl transition-shadow"
                  onClick={() => setShowProofBriefModal(true)}
                >
                  <div className="flex items-center gap-2 px-4 py-2.5 bg-emerald-50 border-b border-emerald-100">
                    <FileCheck className="w-4 h-4 text-emerald-600" />
                    <span className="text-sm font-medium text-emerald-900">Proof Brief Output</span>
                  </div>
                  <div className="p-4 space-y-2">
                    <div className="flex items-center justify-between p-2 rounded bg-emerald-50 border border-emerald-100">
                      <span className="text-xs text-emerald-800">Correctness</span>
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">PROVED</span>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded bg-emerald-50 border border-emerald-100">
                      <span className="text-xs text-emerald-800">Code Quality</span>
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">PROVED</span>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded bg-amber-50 border border-amber-100">
                      <span className="text-xs text-amber-800">Testing</span>
                      <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">PARTIAL</span>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded bg-zinc-50 border border-zinc-200">
                      <span className="text-xs text-zinc-600">Communication</span>
                      <span className="text-[10px] font-bold text-zinc-500 bg-zinc-200 px-1.5 py-0.5 rounded">UNPROVED</span>
                    </div>
                    <p className="text-[10px] text-zinc-400 text-center pt-1">Click to view full brief with interview plan</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* University Carousel */}
      <UniversityCarousel />

      {/* What is the Company Model Section */}
      <section id="company-model" className="py-20 px-4 bg-zinc-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
              The Company Model
            </h2>
            <p className="text-lg text-zinc-600 max-w-2xl mx-auto">
              Not a vibe detector. Not "culture fit." An executable evaluator that generates benchmarks, evaluates evidence, and identifies gaps.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Benchmark Policy */}
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
              <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center mb-4">
                <Target className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-zinc-900 mb-2">Benchmark Policy</h3>
              <p className="text-sm text-zinc-600 mb-4">
                What tasks to run, difficulty, timebox, allowed tools, and scoring dimensions—calibrated to your bar.
              </p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span>Task templates tuned to your stack</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span>Complexity knobs based on role level</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span>AI tool policy configurable</span>
                </div>
              </div>
            </div>

            {/* Evidence Policy */}
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center mb-4">
                <FileCheck className="w-6 h-6 text-emerald-600" />
              </div>
              <h3 className="font-semibold text-zinc-900 mb-2">Evidence Policy</h3>
              <p className="text-sm text-zinc-600 mb-4">
                What counts as proof, what is inadmissible, what must be verified live. Fail-closed by design.
              </p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span>Artifact-backed claims only</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span>No inference, no guessing</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span>Every result links to evidence</span>
                </div>
              </div>
            </div>

            {/* Decision Support */}
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
              <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center mb-4">
                <BarChart3 className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-zinc-900 mb-2">Decision Support</h3>
              <p className="text-sm text-zinc-600 mb-4">
                Gap analysis + interview plan. What remains unproved and exactly how to verify it.
              </p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span>Gaps mapped to your needs</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span>Generated interview questions</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span>Shareable Proof Brief</span>
                </div>
              </div>
            </div>
          </div>

          {/* What it's NOT */}
          <div className="mt-12 p-6 bg-zinc-100 rounded-2xl">
            <h4 className="font-semibold text-zinc-900 mb-4 text-center">What the Company Model is NOT</h4>
            <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 text-sm text-zinc-600">
                <X className="w-4 h-4 text-red-500" />
                <span>"AI decides who to hire"</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-zinc-600">
                <X className="w-4 h-4 text-red-500" />
                <span>A resume ranker</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-zinc-600">
                <X className="w-4 h-4 text-red-500" />
                <span>Personality inference</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-zinc-600">
                <X className="w-4 h-4 text-red-500" />
                <span>"Culture fit" detector</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Statement */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-12">
            Every bad hire costs 6+ months of runway.
          </h2>

          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="text-left">
              <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center mb-4">
                <X className="w-5 h-5 text-red-600" />
              </div>
              <h3 className="font-semibold text-zinc-900 mb-2">Resumes are narrative</h3>
              <p className="text-zinc-600 text-sm leading-relaxed">
                "5 years of Python" says nothing about debugging intuition or code quality. Credentials don't equal capabilities.
              </p>
            </div>
            <div className="text-left">
              <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center mb-4">
                <X className="w-5 h-5 text-red-600" />
              </div>
              <h3 className="font-semibold text-zinc-900 mb-2">Interviews are noisy</h3>
              <p className="text-zinc-600 text-sm leading-relaxed">
                Different interviewers evaluate differently. Same candidate, different outcomes. No consistency.
              </p>
            </div>
            <div className="text-left">
              <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center mb-4">
                <X className="w-5 h-5 text-red-600" />
              </div>
              <h3 className="font-semibold text-zinc-900 mb-2">Generic assessments miss context</h3>
              <p className="text-zinc-600 text-sm leading-relaxed">
                One-size-fits-all tests don't know your bar, your stack, or what "good" means at your company.
              </p>
            </div>
          </div>

          <p className="text-lg text-zinc-600">
            <span className="font-semibold text-zinc-900">Agencity builds your bar into an executable model.</span> Benchmarks calibrated to you. Evidence-bound evaluation. Gap analysis that drives interviews.
          </p>
        </div>
      </section>

      {/* How It Works */}
      <HowItWorks />

      {/* Gap Finding + Candidate Matching */}
      <section className="py-20 px-4 bg-zinc-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
              From gaps to candidates
            </h2>
            <p className="text-lg text-zinc-600 max-w-2xl mx-auto">
              Your Company Model identifies what you're missing. Then find candidates who've already proved it.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Gap Analysis */}
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-amber-600" />
                </div>
                <h3 className="font-semibold text-zinc-900">Gap Analysis</h3>
              </div>
              <p className="text-sm text-zinc-600 mb-4">
                Your Company Model surfaces what's missing from your team and what each role needs to prove.
              </p>
              <div className="space-y-2 p-4 bg-zinc-50 rounded-xl">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-600">"We ship fast but quality is slipping"</span>
                  <span className="text-amber-600 font-medium">→ Gap</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-600">"Need someone to own ambiguous projects"</span>
                  <span className="text-amber-600 font-medium">→ Gap</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-600">"Lack strong test discipline"</span>
                  <span className="text-amber-600 font-medium">→ Gap</span>
                </div>
              </div>
            </div>

            {/* Candidate Matching */}
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                  <Search className="w-5 h-5 text-emerald-600" />
                </div>
                <h3 className="font-semibold text-zinc-900">Candidate Matching</h3>
              </div>
              <p className="text-sm text-zinc-600 mb-4">
                Find candidates who've already proved the skills you need—not match percentages, but verified claims.
              </p>
              <div className="space-y-2 p-4 bg-zinc-50 rounded-xl">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-600">"Show candidates who proved testing depth"</span>
                  <span className="text-emerald-600 font-medium">→ 12 found</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-600">"Who handled ambiguous debugging tasks?"</span>
                  <span className="text-emerald-600 font-medium">→ 8 found</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-600">"Quality-focused with fast shipping"</span>
                  <span className="text-emerald-600 font-medium">→ 5 found</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Differentiation Table */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
              Not another assessment tool.
            </h2>
            <p className="text-lg text-zinc-600">
              We build your evaluation model. They run generic tests.
            </p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-zinc-200">
            <table className="w-full">
              <thead className="bg-zinc-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-900"></th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-zinc-500">Generic Tools</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-zinc-900 bg-emerald-50">Agencity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200">
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-zinc-900">Core product</td>
                  <td className="px-6 py-4 text-sm text-zinc-600 text-center">Assessment platform</td>
                  <td className="px-6 py-4 text-sm text-zinc-900 text-center bg-emerald-50 font-medium">Company Model + Evaluation</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-zinc-900">Benchmarks</td>
                  <td className="px-6 py-4 text-sm text-zinc-600 text-center">Generic puzzles</td>
                  <td className="px-6 py-4 text-sm text-zinc-900 text-center bg-emerald-50 font-medium">Calibrated to your bar</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-zinc-900">Output</td>
                  <td className="px-6 py-4 text-sm text-zinc-600 text-center">Score (0-100)</td>
                  <td className="px-6 py-4 text-sm text-zinc-900 text-center bg-emerald-50 font-medium">Proof Brief + gap analysis</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-zinc-900">Learning</td>
                  <td className="px-6 py-4 text-sm text-zinc-600 text-center">Static</td>
                  <td className="px-6 py-4 text-sm text-zinc-900 text-center bg-emerald-50 font-medium">Adapts from preferences</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-zinc-900">Gap finding</td>
                  <td className="px-6 py-4 text-sm text-zinc-600 text-center">No</td>
                  <td className="px-6 py-4 text-sm text-zinc-900 text-center bg-emerald-50 font-medium">Team + role gap analysis</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section id="trust" className="py-20 px-4 bg-zinc-900 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4">
            Evidence-bound. Auditable. Defensible.
          </h2>
          <p className="text-lg text-zinc-400 mb-12 max-w-2xl mx-auto">
            The proof engine is the safety rail. No hidden signals. Every claim links to artifacts.
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mx-auto mb-4">
                <Shield className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="font-semibold mb-2">Fail-closed evaluation</h3>
              <p className="text-sm text-zinc-400">No proof = no claim. The model can only score over admissible evidence. No invented signals.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mx-auto mb-4">
                <FileCheck className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="font-semibold mb-2">Consistent rubric + audit logs</h3>
              <p className="text-sm text-zinc-400">Same criteria for every candidate. Full audit trail. Every result traceable to artifacts.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mx-auto mb-4">
                <Zap className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="font-semibold mb-2">Adaptive, not black-box</h3>
              <p className="text-sm text-zinc-400">Active evaluation chooses the next best benchmark to reduce uncertainty—transparently.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Dual-sided Section */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-8">
            <div className="p-8 rounded-2xl border border-zinc-200 bg-zinc-50">
              <h3 className="text-xl font-semibold text-zinc-900 mb-4">For startups</h3>
              <p className="text-zinc-600 mb-6">
                Build your hiring bar into an executable model. Generate calibrated benchmarks. Get gap analysis + interview plans. Find candidates who've proved what you need.
              </p>
              <button
                onClick={handleGetStarted}
                className="inline-flex items-center text-sm font-semibold text-zinc-900 hover:text-zinc-700"
              >
                Build your Company Model
                <ArrowRight className="ml-2 w-4 h-4" />
              </button>
            </div>
            <div className="p-8 rounded-2xl border border-zinc-200 bg-zinc-50">
              <h3 className="text-xl font-semibold text-zinc-900 mb-4">For candidates</h3>
              <p className="text-zinc-600 mb-6">
                Get hired for what you can do, not what you claim. Complete evaluations, build a proof profile, and match to companies where your skills are actually needed.
              </p>
              <button
                onClick={handleGetStarted}
                className="inline-flex items-center text-sm font-semibold text-zinc-900 hover:text-zinc-700"
              >
                Join the talent network
                <ArrowRight className="ml-2 w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq">
        <FAQ />
      </section>

      {/* Final CTA / Waitlist */}
      <section id="waitlist" className="py-20 px-4 bg-zinc-50">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
            Make your hiring bar executable.
          </h2>
          <p className="text-lg text-zinc-600 mb-8">
            Build your Company Model. Generate calibrated benchmarks. Hire with proof.
          </p>

          <form onSubmit={handleSubmitWaitlist} className="max-w-md mx-auto">
            <div className="flex flex-col sm:flex-row gap-3 mb-4">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="flex-1 px-4 py-3 rounded-xl border border-zinc-300 focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900 outline-none transition-colors"
              />
              <button
                type="submit"
                className="px-6 py-3 rounded-xl bg-zinc-900 text-white font-semibold hover:bg-zinc-800 transition-colors"
              >
                Request Access
              </button>
            </div>
            <div className="flex items-center justify-center gap-4 text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="userType"
                  checked={userType === "founder"}
                  onChange={() => setUserType("founder")}
                  className="w-4 h-4 text-zinc-900"
                />
                <span className="text-zinc-600">I'm a founder</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="userType"
                  checked={userType === "candidate"}
                  onChange={() => setUserType("candidate")}
                  className="w-4 h-4 text-zinc-900"
                />
                <span className="text-zinc-600">I'm a candidate</span>
              </label>
            </div>
          </form>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-10">
          <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center">
            <div>
              <p className="text-sm font-semibold text-zinc-900">Agencity</p>
              <p className="mt-1 text-sm text-zinc-500">Your Company Model for hiring.</p>
            </div>
            <div className="flex gap-5 text-sm text-zinc-500">
              <a href="#company-model" className="hover:text-zinc-900 transition-colors">Company Model</a>
              <a href="#how-it-works" className="hover:text-zinc-900 transition-colors">How it works</a>
              <a href="#faq" className="hover:text-zinc-900 transition-colors">FAQ</a>
            </div>
          </div>
          <p className="mt-8 text-xs text-zinc-400">&copy; {currentYear} Agencity. All rights reserved.</p>
        </div>
      </footer>

      {/* Proof Brief Modal */}
      <ProofBriefModal open={showProofBriefModal} onClose={() => setShowProofBriefModal(false)} />
    </div>
  );
}
