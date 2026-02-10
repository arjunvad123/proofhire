"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus } from "lucide-react";

interface FAQItem {
  question: string;
  answer: React.ReactNode;
}

const faqs: FAQItem[] = [
  {
    question: "What exactly is the 'Company Model'?",
    answer: (
      <div className="space-y-3 text-sm">
        <p>The Company Model is an executable evaluator + benchmark generator calibrated to your hiring bar. It outputs three things:</p>
        <ul className="list-disc pl-4 space-y-1 text-zinc-700">
          <li><strong>Benchmark Policy</strong> — What tasks to run, difficulty, timebox, allowed tools, scoring dimensions.</li>
          <li><strong>Evidence Policy</strong> — What counts as proof, what's inadmissible, what must be verified live.</li>
          <li><strong>Decision Support</strong> — Gap analysis + interview plan for what remains unproved.</li>
        </ul>
        <p>It's not a vibe detector, not "culture fit," and not a black-box ranker. It's your bar, made executable.</p>
      </div>
    ),
  },
  {
    question: "How do you learn my company's bar with limited data?",
    answer: (
      <div className="space-y-3 text-sm">
        <p>We don't need thousands of hires. The Company Model learns from:</p>
        <ul className="list-disc pl-4 space-y-1 text-zinc-700">
          <li><strong>15-minute calibration</strong> — Your pace, quality bar, autonomy expectations.</li>
          <li><strong>2-5 exemplar PRs or style guides</strong> (optional) — What "good" looks like here.</li>
          <li><strong>Preference labels</strong> — Pairwise comparisons: "Candidate A vs B for our bar."</li>
        </ul>
        <p>The model adapts from your feedback, not from outcome-trained ML that requires scale you don't have.</p>
      </div>
    ),
  },
  {
    question: "How is this different from HackerRank / CodeSignal?",
    answer: (
      <div className="space-y-3 text-sm">
        <p>They run generic assessments and output a score.</p>
        <p className="font-medium text-zinc-900">We build your Company Model, generate calibrated benchmarks, and output Proof Briefs with evidence links.</p>
        <ul className="list-disc pl-4 space-y-1 text-zinc-700">
          <li>Their tests are one-size-fits-all. Ours are tuned to your bar.</li>
          <li>They give you a number. We show you what's proved and what isn't.</li>
          <li>They're static. Our model adapts from your preferences.</li>
        </ul>
      </div>
    ),
  },
  {
    question: "Can candidates use AI tools?",
    answer: (
      <div className="space-y-3 text-sm">
        <p className="font-medium text-zinc-900">Configurable per company. Many startups allow AI—so we're built for it.</p>
        <p>The Company Model's evidence policy defines what's allowed. We evaluate:</p>
        <ul className="list-disc pl-4 space-y-1 text-zinc-700">
          <li>How they integrate AI into their workflow</li>
          <li>Whether they catch and correct mistakes</li>
          <li>Whether they understand what they're shipping</li>
        </ul>
        <p>This gives a stronger signal than banning tools.</p>
      </div>
    ),
  },
  {
    question: "What's 'fail-closed' and why does it matter?",
    answer: (
      <div className="space-y-3 text-sm">
        <p><strong>Fail-closed</strong> means: no proof = no claim. The Company Model can only score over admissible evidence features. It cannot invent hidden signals.</p>
        <p>Why this matters:</p>
        <ul className="list-disc pl-4 space-y-1 text-zinc-700">
          <li>Every claim links to an artifact (diff, test log, coverage report)</li>
          <li>No guessing, no inference, no black-box scoring</li>
          <li>Defensible decisions with full audit trail</li>
        </ul>
        <p>The proof engine is the safety rail that makes the system trustworthy.</p>
      </div>
    ),
  },
  {
    question: "How does the 'reasoning engine' work?",
    answer: (
      <div className="space-y-3 text-sm">
        <p>Most AI hiring tools do pattern matching: "resume has Python → +10 points." We train our model differently using <strong>actor-critic reinforcement learning</strong>.</p>
        <p className="font-medium text-zinc-900">The model learns to reason through evaluations:</p>
        <ul className="list-disc pl-4 space-y-1 text-zinc-700">
          <li><strong>Actor</strong> — Proposes a reasoning chain: "This diff shows systematic debugging → test added → PROVED"</li>
          <li><strong>Critic</strong> — Evaluates the reasoning: "Chain valid, but communication lacks artifact → UNPROVED"</li>
          <li><strong>Training signal</strong> — Model improves at constructing valid proof chains, not just matching keywords</li>
        </ul>
        <p>The result: a model that reasons like your best hiring manager, not a keyword counter.</p>
      </div>
    ),
  },
  {
    question: "What about finding candidates who match our gaps?",
    answer: (
      <div className="space-y-3 text-sm">
        <p>Once you've built your Company Model, it surfaces what you're missing:</p>
        <ul className="list-disc pl-4 space-y-1 text-zinc-700">
          <li>"We ship fast but quality is slipping" → Gap identified</li>
          <li>"Need someone to own ambiguous projects" → Role spec generated</li>
          <li>"Lack strong test discipline" → Benchmark to detect it</li>
        </ul>
        <p>Then you can search: "Show me candidates who proved testing depth and debugging ability"—not match percentages, but verified claims.</p>
      </div>
    ),
  },
];

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="py-20 px-4 bg-white border-t border-zinc-100">
      <div className="max-w-5xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16">
          {/* Left Column - Header */}
          <div className="lg:col-span-4">
            <div className="lg:sticky lg:top-24">
              <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
                Frequently Asked Questions
              </h2>
              <p className="text-lg text-zinc-500">
                Common questions about the Company Model and how Agencity works.
              </p>
            </div>
          </div>

          {/* Right Column - Accordion */}
          <div className="lg:col-span-8 space-y-3">
            {faqs.map((faq, index) => {
              const isOpen = openIndex === index;

              return (
                <div
                  key={index}
                  className={`border rounded-2xl overflow-hidden transition-all duration-300 ${
                    isOpen
                      ? "border-zinc-200 shadow-lg"
                      : "border-zinc-100 bg-zinc-50/50 hover:bg-white hover:border-zinc-200 hover:shadow-md"
                  }`}
                >
                  <button
                    onClick={() => setOpenIndex(isOpen ? null : index)}
                    className="w-full flex items-center justify-between p-6 text-left focus:outline-none group"
                  >
                    <span className="text-base md:text-lg font-medium text-zinc-900 pr-8">
                      {faq.question}
                    </span>
                    <span className="flex-shrink-0 relative w-6 h-6 flex items-center justify-center">
                      <motion.div
                        animate={{ rotate: isOpen ? 45 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <Plus className={`w-5 h-5 transition-colors duration-200 ${
                          isOpen ? "text-zinc-900" : "text-zinc-400 group-hover:text-zinc-600"
                        }`} />
                      </motion.div>
                    </span>
                  </button>

                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3, ease: [0.04, 0.62, 0.23, 0.98] }}
                      >
                        <div className="px-6 pb-6 pt-0">
                          <div className="border-t border-zinc-100 pt-4">
                            <div className="text-zinc-600 leading-relaxed">
                              {faq.answer}
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
