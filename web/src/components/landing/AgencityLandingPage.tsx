"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useScroll, useTransform, motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { HowItWorks } from "./HowItWorks";
import { FAQ } from "./FAQ";
import { UniversityCarousel } from "./UniversityCarousel";
import { ProofBriefModal } from "./ProofBriefModal";
import { Check, Shield, FileCheck, Clock, ArrowRight, X } from "lucide-react";

export function AgencityLandingPage() {
  const router = useRouter();
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
    // TODO: Submit to backend
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
          {/* Shimmer Effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent pointer-events-none skew-x-12" />

          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 pl-2 transition-opacity hover:opacity-80 relative z-10">
            <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
              <Check className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold text-white tracking-tight">Agencity</span>
          </Link>

          {/* Navigation - Desktop */}
          <nav className="hidden md:flex items-center gap-6 relative z-10">
            <a href="#how-it-works" className="text-sm font-medium text-white/70 hover:text-white transition-colors">How it works</a>
            <a href="#proof-brief" className="text-sm font-medium text-white/70 hover:text-white transition-colors">Proof Brief</a>
            <a href="#trust" className="text-sm font-medium text-white/70 hover:text-white transition-colors">Trust</a>
            <a href="#faq" className="text-sm font-medium text-white/70 hover:text-white transition-colors">FAQ</a>
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-3 pr-1 relative z-10">
            <Button
              onClick={handleGetStarted}
              className="rounded-full px-5 sm:px-6 py-1.5 sm:py-2 text-xs sm:text-sm font-semibold text-black bg-white hover:bg-gray-100 transition-all duration-300 transform hover:scale-105"
            >
              Request Access
            </Button>

            {/* Mobile Menu Toggle */}
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

        {/* Mobile Menu */}
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
                <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-3 text-base font-medium text-white/80 hover:bg-white/10 hover:text-white rounded-xl transition-colors">How it works</a>
                <a href="#proof-brief" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-3 text-base font-medium text-white/80 hover:bg-white/10 hover:text-white rounded-xl transition-colors">Proof Brief</a>
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

      {/* Hero Section */}
      <section className="relative pt-32 pb-12 overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-slate-50 via-white to-white z-0" />

        <div className="relative z-10 mx-auto max-w-6xl px-4">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            {/* Left: Copy */}
            <div>
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-semibold leading-tight tracking-tight text-zinc-900">
                Hire with proof.
              </h1>

              <p className="mt-6 max-w-xl text-lg leading-relaxed text-zinc-600 md:text-xl">
                Company-calibrated work samples that produce an evidence-backed brief—what's proven, what isn't, and what to ask next.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <button
                  onClick={handleGetStarted}
                  className="inline-flex items-center justify-center rounded-xl bg-zinc-900 px-6 py-3.5 text-sm font-semibold text-white hover:bg-zinc-800 transition-colors shadow-lg shadow-zinc-900/10"
                >
                  Request early access
                  <ArrowRight className="ml-2 w-4 h-4" />
                </button>
                <button
                  onClick={() => setShowProofBriefModal(true)}
                  className="inline-flex items-center justify-center rounded-xl border border-zinc-200 bg-white px-6 py-3.5 text-sm font-semibold text-zinc-900 hover:bg-zinc-50 hover:border-zinc-300 transition-colors"
                >
                  See a sample Proof Brief
                </button>
              </div>

              {/* Social proof */}
              <div className="mt-8 flex items-center gap-6 text-sm text-zinc-500">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-emerald-600" />
                  <span>Secure sandbox</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-emerald-600" />
                  <span>5-8 min review</span>
                </div>
                <div className="flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-emerald-600" />
                  <span>Fail-closed</span>
                </div>
              </div>
            </div>

            {/* Right: Proof Brief Preview */}
            <div className="relative">
              <div className="absolute -inset-4 rounded-3xl bg-gradient-to-r from-emerald-500/10 via-sky-400/10 to-amber-500/10 blur-2xl" />
              <div
                className="relative rounded-2xl border border-zinc-200 bg-white shadow-xl overflow-hidden cursor-pointer hover:shadow-2xl transition-shadow"
                onClick={() => setShowProofBriefModal(true)}
              >
                {/* Mini top bar */}
                <div className="flex items-center gap-2 px-4 py-2.5 bg-zinc-50 border-b border-zinc-200">
                  <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  </div>
                  <div className="flex-1 mx-3 h-5 bg-white rounded border border-zinc-200 flex items-center px-2">
                    <span className="text-[10px] text-zinc-400">Proof Brief — Senior Backend Engineer</span>
                  </div>
                </div>

                <div className="p-6">
                  {/* Header */}
                  <div className="flex items-center gap-4 mb-6 pb-4 border-b border-zinc-100">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-zinc-200 to-zinc-300 flex items-center justify-center text-zinc-500 font-semibold">
                      AC
                    </div>
                    <div>
                      <p className="font-semibold text-zinc-900">Anonymous Candidate</p>
                      <p className="text-sm text-zinc-500">Completed 87 minutes ago</p>
                    </div>
                  </div>

                  {/* Claims Grid */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                      <span className="text-sm font-medium text-emerald-900">Correctness</span>
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-1 rounded">PROVED</span>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                      <span className="text-sm font-medium text-emerald-900">Code Quality</span>
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-1 rounded">PROVED</span>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg bg-amber-50 border border-amber-200">
                      <span className="text-sm font-medium text-amber-900">Testing Habits</span>
                      <span className="text-xs font-bold text-amber-700 bg-amber-100 px-2 py-1 rounded">PARTIAL</span>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-50 border border-zinc-200">
                      <span className="text-sm font-medium text-zinc-700">Communication</span>
                      <span className="text-xs font-bold text-zinc-600 bg-zinc-100 px-2 py-1 rounded">UNPROVED</span>
                    </div>
                  </div>

                  {/* Interview prompts teaser */}
                  <div className="mt-4 pt-4 border-t border-zinc-100">
                    <p className="text-xs text-zinc-500 mb-2">Suggested interview focus:</p>
                    <p className="text-sm text-zinc-700">Walk through edge case handling...</p>
                  </div>

                  {/* Click to expand */}
                  <div className="mt-4 text-center">
                    <span className="text-xs text-zinc-400">Click to view full brief</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* University Carousel */}
      <UniversityCarousel />

      {/* Pain -> Relief Section */}
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
              <h3 className="font-semibold text-zinc-900 mb-2">Bad hires burn runway</h3>
              <p className="text-zinc-600 text-sm leading-relaxed">
                When your team is 6 people, one weak hire creates drag everywhere: code quality, velocity, morale.
              </p>
            </div>
          </div>

          <p className="text-lg text-zinc-600">
            <span className="font-semibold text-zinc-900">Agencity turns hiring into evidence.</span> See exactly what candidates have proven—before the first call.
          </p>
        </div>
      </section>

      {/* How It Works */}
      <HowItWorks />

      {/* Proof Brief Section */}
      <section id="proof-brief" className="py-20 px-4 bg-zinc-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
              The Proof Brief
            </h2>
            <p className="text-lg text-zinc-600 max-w-2xl mx-auto">
              A shareable, 1-page hiring packet. Forward it to your co-founder.
              Every claim links to evidence. Every gap comes with interview prompts.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8 items-center">
            {/* Left: Features */}
            <div className="space-y-6">
              <div className="flex gap-4">
                <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
                  <Check className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-900 mb-1">PROVED claims with evidence links</h3>
                  <p className="text-zinc-600 text-sm">Every green badge links directly to diffs, test logs, or coverage reports.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <FileCheck className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-900 mb-1">UNPROVED claims with interview prompts</h3>
                  <p className="text-zinc-600 text-sm">Know exactly what to verify in your 30-minute call. No more generic questions.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <Clock className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-900 mb-1">5-8 minute review time</h3>
                  <p className="text-zinc-600 text-sm">Replace hour-long debriefs with a focused decision packet you can review between meetings.</p>
                </div>
              </div>
            </div>

            {/* Right: Sample brief button */}
            <div className="text-center lg:text-left">
              <button
                onClick={() => setShowProofBriefModal(true)}
                className="inline-flex items-center justify-center rounded-xl bg-zinc-900 px-8 py-4 text-base font-semibold text-white hover:bg-zinc-800 transition-colors shadow-lg"
              >
                View sample Proof Brief
                <ArrowRight className="ml-2 w-5 h-5" />
              </button>
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
              We produce evidence packets, not mystery scores.
            </p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-zinc-200">
            <table className="w-full">
              <thead className="bg-zinc-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-900"></th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-zinc-500">HackerRank / CodeSignal</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-zinc-900 bg-emerald-50">Agencity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200">
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-zinc-900">What's evaluated</td>
                  <td className="px-6 py-4 text-sm text-zinc-600 text-center">Algorithmic puzzles</td>
                  <td className="px-6 py-4 text-sm text-zinc-900 text-center bg-emerald-50 font-medium">Real work samples</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-zinc-900">Output</td>
                  <td className="px-6 py-4 text-sm text-zinc-600 text-center">Score (0-100)</td>
                  <td className="px-6 py-4 text-sm text-zinc-900 text-center bg-emerald-50 font-medium">Evidence packet + interview plan</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-zinc-900">Customization</td>
                  <td className="px-6 py-4 text-sm text-zinc-600 text-center">Generic bar</td>
                  <td className="px-6 py-4 text-sm text-zinc-900 text-center bg-emerald-50 font-medium">Your bar, your rubric</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-zinc-900">Defensibility</td>
                  <td className="px-6 py-4 text-sm text-zinc-600 text-center">Black box</td>
                  <td className="px-6 py-4 text-sm text-zinc-900 text-center bg-emerald-50 font-medium">Every result links to artifacts</td>
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
            Built for defensible decisions.
          </h2>
          <p className="text-lg text-zinc-400 mb-12 max-w-2xl mx-auto">
            Every hiring decision should be traceable. Agencity is fail-closed by design.
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mx-auto mb-4">
                <Shield className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="font-semibold mb-2">Fail-closed evaluation</h3>
              <p className="text-sm text-zinc-400">No proof = no claim. We don't guess or infer. Every assertion links to evidence.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mx-auto mb-4">
                <FileCheck className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="font-semibold mb-2">Consistent rubric + audit logs</h3>
              <p className="text-sm text-zinc-400">Same criteria applied to every candidate. Full audit trail for compliance review.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mx-auto mb-4">
                <Clock className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="font-semibold mb-2">Secure sandbox execution</h3>
              <p className="text-sm text-zinc-400">Docker-isolated, resource-limited, deterministic grading. No data leakage.</p>
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
                Move fast without lowering the bar. Get consistent, defensible hiring decisions in minutes—not weeks.
              </p>
              <button
                onClick={handleGetStarted}
                className="inline-flex items-center text-sm font-semibold text-zinc-900 hover:text-zinc-700"
              >
                Request founder access
                <ArrowRight className="ml-2 w-4 h-4" />
              </button>
            </div>
            <div className="p-8 rounded-2xl border border-zinc-200 bg-zinc-50">
              <h3 className="text-xl font-semibold text-zinc-900 mb-4">For candidates</h3>
              <p className="text-zinc-600 mb-6">
                Get hired for what you can do, not what you claim. Complete one assessment, build a reusable proof profile.
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
            Stop guessing. Start hiring with proof.
          </h2>
          <p className="text-lg text-zinc-600 mb-8">
            Join early-stage founders building teams based on evidence.
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
              <p className="mt-1 text-sm text-zinc-500">Evidence-first hiring for early startups.</p>
            </div>
            <div className="flex gap-5 text-sm text-zinc-500">
              <a href="#how-it-works" className="hover:text-zinc-900 transition-colors">How it works</a>
              <a href="#proof-brief" className="hover:text-zinc-900 transition-colors">Proof Brief</a>
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
