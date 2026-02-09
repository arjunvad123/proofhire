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
    question: "How is this different from HackerRank / CodeSignal?",
    answer: (
      <div className="space-y-3 text-sm">
        <p>They mostly measure generic problem-solving with algorithmic puzzles.</p>
        <p className="font-medium text-zinc-900">
          Agencity measures job-relevant work and outputs a Proof Brief with evidence links—not a mystery score.
        </p>
        <p>You see exactly what was proven and what wasn't, with artifacts you can review yourself.</p>
      </div>
    ),
  },
  {
    question: "What exactly are you evaluating?",
    answer: (
      <div className="space-y-3 text-sm">
        <p>We evaluate what the work proves across four dimensions:</p>
        <ul className="list-disc pl-4 space-y-1 text-zinc-700">
          <li><strong>Correctness</strong> — Does it work? Tests pass, edge cases handled.</li>
          <li><strong>Testing habits</strong> — Coverage, quality of test cases.</li>
          <li><strong>Code quality</strong> — Structure, readability, maintainability.</li>
          <li><strong>Communication</strong> — Written reasoning, tradeoff notes.</li>
        </ul>
        <p>Every evaluation links to artifacts: diffs, test logs, coverage reports.</p>
      </div>
    ),
  },
  {
    question: "Can candidates use AI tools?",
    answer: (
      <div className="space-y-3 text-sm">
        <p className="font-medium text-zinc-900">Configurable by company. Many startups allow AI—so we're built for it.</p>
        <p>We evaluate engineering judgment, verification, and quality—not memorization. We measure:</p>
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
    question: "How long does it take candidates?",
    answer: (
      <div className="space-y-3 text-sm">
        <p>Typically <strong>60-90 minutes</strong>.</p>
        <p>It's designed to be bounded and comparable—closer to real work than an open-ended take-home that drags on for days.</p>
      </div>
    ),
  },
  {
    question: "What is a 'Proof Brief'?",
    answer: (
      <div className="space-y-3 text-sm">
        <p>A shareable, 1-page hiring packet showing:</p>
        <ul className="list-disc pl-4 space-y-1 text-zinc-700">
          <li><strong>PROVED claims</strong> — with links to evidence (diffs, tests, coverage)</li>
          <li><strong>UNPROVED claims</strong> — with suggested interview questions</li>
          <li><strong>Interview plan</strong> — exactly what to verify in your 30-min call</li>
        </ul>
        <p>Forward it to your co-founder. Review it in 5-8 minutes. Make a defensible decision.</p>
      </div>
    ),
  },
  {
    question: "Is this compliant / legally defensible?",
    answer: (
      <div className="space-y-3 text-sm">
        <p>We focus on <strong>job-relevant evidence</strong> from the work sample, not proxies or claims.</p>
        <p>We apply a consistent rubric with full audit logs. Every result links back to artifacts.</p>
        <p>This is the foundation for defensible hiring decisions—you can show exactly why you made each call.</p>
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
                Common questions about hiring with Agencity.
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
