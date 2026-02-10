"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Cpu, Check, Send, Users, Zap, Search, ChevronDown, X, Target, MapPin, Github, BookOpen, Trophy, Loader2, MessageSquare } from "lucide-react";

// Demo conversation flow
const demoConversations: Record<string, { question: string; options?: string[] }[]> = {
  default: [
    { question: "What role are you hiring for?", options: ["Prompt engineer", "Backend engineer", "Hardware engineer", "Something else"] },
  ],
  "prompt engineer": [
    { question: "Got it. What does your startup do, and what will this person actually be working on?" },
    { question: "Helpful. A few more questions:\n\n• Is this more research-y or production-focused?\n• What would success look like by day 60?\n• Any past hires or interviews that went well—or didn't?" },
    { question: "Last one: Any location/school preferences or constraints?" },
  ],
  "backend engineer": [
    { question: "Got it. What does your startup do, and what kind of backend work?" },
    { question: "Helpful. A few more questions:\n\n• What's the scale you're building for?\n• Any specific tech stack requirements?\n• What would success look like by day 60?" },
    { question: "Last one: Any location/school preferences or constraints?" },
  ],
  "hardware engineer": [
    { question: "Got it. What kind of hardware—embedded, RF, mechanical, PCB?" },
    { question: "Helpful. A few more questions:\n\n• Prototype stage or production/manufacturing?\n• Any compliance requirements (FCC, UL, etc.)?\n• What would success look like by day 60?" },
    { question: "Last one: Any location/school preferences or constraints?" },
  ],
};

export function AgencityLandingPage() {
  const [email, setEmail] = useState("");

  // Demo state
  const [demoStarted, setDemoStarted] = useState(false);
  const [demoStep, setDemoStep] = useState(0);
  const [demoPath, setDemoPath] = useState("default");
  const [demoMessages, setDemoMessages] = useState<{ role: "agent" | "user"; content: string }[]>([]);
  const [userInput, setUserInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [searchingStep, setSearchingStep] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // FAQ state
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const handleSubmitWaitlist = (e: React.FormEvent) => {
    e.preventDefault();
    alert(`Thanks! We'll be in touch at ${email}`);
    setEmail("");
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [demoMessages]);

  const startDemo = () => {
    setDemoStarted(true);
    setDemoStep(0);
    setDemoPath("default");
    setDemoMessages([]);
    setShowResults(false);
    setSearchingStep(0);

    // Add first agent message
    setTimeout(() => {
      setDemoMessages([{ role: "agent", content: "What role are you hiring for?" }]);
    }, 500);
  };

  const handleDemoOption = (option: string) => {
    const lowerOption = option.toLowerCase();
    setDemoMessages(prev => [...prev, { role: "user", content: option }]);

    if (demoPath === "default") {
      // Set the conversation path based on selection
      const path = lowerOption.includes("prompt") ? "prompt engineer" :
                   lowerOption.includes("backend") ? "backend engineer" :
                   lowerOption.includes("hardware") ? "hardware engineer" : "prompt engineer";
      setDemoPath(path);
      setDemoStep(0);

      // Add next agent question after delay
      setIsTyping(true);
      setTimeout(() => {
        setIsTyping(false);
        const questions = demoConversations[path];
        if (questions && questions[0]) {
          setDemoMessages(prev => [...prev, { role: "agent", content: questions[0].question }]);
        }
      }, 1000);
    }
  };

  const handleDemoSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    setDemoMessages(prev => [...prev, { role: "user", content: userInput }]);
    setUserInput("");

    const questions = demoConversations[demoPath];
    const nextStep = demoStep + 1;

    if (nextStep < questions.length) {
      setIsTyping(true);
      setTimeout(() => {
        setIsTyping(false);
        setDemoMessages(prev => [...prev, { role: "agent", content: questions[nextStep].question }]);
        setDemoStep(nextStep);
      }, 1200);
    } else {
      // Start searching animation
      setIsTyping(true);
      setTimeout(() => {
        setIsTyping(false);
        setDemoMessages(prev => [...prev, { role: "agent", content: "Got it. I have enough context. Let me search..." }]);

        // Animate through search steps
        const searchSteps = [1, 2, 3, 4, 5, 6];
        searchSteps.forEach((step, index) => {
          setTimeout(() => {
            setSearchingStep(step);
            if (step === 6) {
              setTimeout(() => setShowResults(true), 800);
            }
          }, 600 * (index + 1));
        });
      }, 800);
    }
  };

  const searchSources = [
    { name: "Our network (6,000+)", icon: Users },
    { name: "University clubs & orgs", icon: BookOpen },
    { name: "GitHub activity", icon: Github },
    { name: "Hackathon participants", icon: Trophy },
    { name: "Course signals", icon: BookOpen },
    { name: "Referral network", icon: Users },
  ];

  const sampleCandidates = [
    {
      name: "Maya Patel",
      tagline: "UCSD · CS Junior",
      knownFacts: [
        "UCSD Computer Science, Class of 2026",
        "Member of Triton AI club",
        "Took CSE 151B (ML), CSE 150A (AI)",
      ],
      observedSignals: [
        "GitHub: 2 ML projects, 1 with LLM API calls",
        "SD Hacks: Built chatbot project (won category prize)",
        "Active: 47 commits in last 3 months",
      ],
      unknown: [
        "Actual prompt engineering depth",
        "Shipping speed / work style",
        "Interest in early-stage startup",
      ],
      whyConsider: "Local (UCSD), ML background, active builder, has touched LLM APIs",
      nextStep: "Coffee chat: ask about her hackathon project and interest in startups",
    },
    {
      name: "James Chen",
      tagline: "UCSD · CS Senior",
      knownFacts: [
        "UCSD Computer Science, Class of 2025",
        "Research assistant in NLP lab",
        "Published paper on few-shot learning",
      ],
      observedSignals: [
        "GitHub: Fine-tuning experiments, prompt optimization repo",
        "TA for CSE 256 (NLP course)",
        "Contributor to open-source LLM project",
      ],
      unknown: [
        "Production experience (mostly research)",
        "Startup pace tolerance",
        "Availability timeline",
      ],
      whyConsider: "Deep NLP knowledge, has optimized prompts for research, local",
      nextStep: "Ask about production vs research preference, graduation plans",
    },
    {
      name: "Sofia Rodriguez",
      tagline: "UCSD · Data Science Junior",
      knownFacts: [
        "UCSD Data Science, Class of 2026",
        "The Basement (UCSD incubator) participant",
        "Built side project with GPT API",
      ],
      observedSignals: [
        "Shipped 2 side projects in last year",
        "Active in startup community events",
        "GitHub shows iteration speed (many commits)",
      ],
      unknown: [
        "Technical depth on prompts/evals",
        "ML fundamentals",
        "Team collaboration style",
      ],
      whyConsider: "Startup-minded, ships fast, already in founder community",
      nextStep: "Ask about her side projects, what she'd want to learn",
    },
  ];

  return (
    <div className="min-h-screen bg-white text-zinc-900 font-sans">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-zinc-100">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-zinc-900">Agencity</span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            <a href="#problem" className="text-sm text-zinc-600 hover:text-zinc-900 transition-colors">Problem</a>
            <a href="#how-it-works" className="text-sm text-zinc-600 hover:text-zinc-900 transition-colors">How it works</a>
            <a href="#demo" className="text-sm text-zinc-600 hover:text-zinc-900 transition-colors">Try it</a>
          </nav>

          <Button
            onClick={() => document.getElementById("waitlist")?.scrollIntoView({ behavior: "smooth" })}
            className="bg-zinc-900 text-white font-medium px-5 py-2 rounded-full hover:bg-zinc-800 transition-colors"
          >
            Request Access
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="min-h-screen flex flex-col items-center justify-center text-center px-6 pt-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl"
        >
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold mb-6 text-zinc-900 tracking-tight">
            Find the people
            <br />
            <span className="text-emerald-600">you can't search for.</span>
          </h1>

          <p className="text-xl md:text-2xl text-zinc-600 mb-6 max-w-2xl mx-auto leading-relaxed">
            Tell us what you need—even if it's vague. We'll find candidates others miss, and tell you honestly what we know vs. what you'll need to verify.
          </p>

          <p className="text-sm text-zinc-500 mb-10">
            Built for early-stage founders who don't have time to source.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={() => document.getElementById("demo")?.scrollIntoView({ behavior: "smooth" })}
              className="bg-zinc-900 text-white font-semibold px-8 py-4 rounded-full text-lg hover:bg-zinc-800 transition-colors"
            >
              Try the Demo
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button
              onClick={() => document.getElementById("waitlist")?.scrollIntoView({ behavior: "smooth" })}
              variant="outline"
              className="border-zinc-300 text-zinc-900 px-8 py-4 rounded-full text-lg hover:bg-zinc-50 transition-colors"
            >
              Request Access
            </Button>
          </div>

          <div className="mt-12 text-sm text-zinc-500">
            6,000+ candidates in our network
          </div>
        </motion.div>

        <motion.div
          className="absolute bottom-10"
          animate={{ y: [0, 10, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
        >
          <div className="w-6 h-10 border-2 border-zinc-300 rounded-full flex justify-center pt-2">
            <div className="w-1.5 h-3 bg-zinc-400 rounded-full" />
          </div>
        </motion.div>
      </section>

      {/* Problem Section */}
      <section id="problem" className="py-24 px-6 bg-zinc-50 border-y border-zinc-100">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
              The best candidates aren't searchable.
            </h2>
            <p className="text-lg text-zinc-600 max-w-2xl mx-auto">
              A brilliant CS junior at UCSD doesn't have a polished LinkedIn. They're in a club, have a sparse GitHub, and aren't "open to work."
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl border border-zinc-200 p-6">
              <h3 className="font-semibold text-zinc-900 mb-4">What traditional search finds:</h3>
              <ul className="space-y-3 text-zinc-600">
                <li className="flex items-start gap-2">
                  <X className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                  <span>People with optimized profiles</span>
                </li>
                <li className="flex items-start gap-2">
                  <X className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                  <span>People actively job hunting</span>
                </li>
                <li className="flex items-start gap-2">
                  <X className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                  <span>People who match keywords</span>
                </li>
              </ul>
            </div>

            <div className="bg-white rounded-2xl border border-emerald-200 p-6">
              <h3 className="font-semibold text-zinc-900 mb-4">What you actually need:</h3>
              <ul className="space-y-3 text-zinc-600">
                <li className="flex items-start gap-2">
                  <Check className="w-5 h-5 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <span>People who could be great at this</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="w-5 h-5 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <span>People who aren't obviously visible</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="w-5 h-5 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <span>People worth a 30-minute conversation</span>
                </li>
              </ul>
            </div>
          </div>

          <p className="text-center mt-12 text-zinc-500">
            We search deeper, tell you what we found, and let you decide who to talk to.
          </p>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
              How it works
            </h2>
          </div>

          <div className="max-w-3xl mx-auto space-y-12">
            {/* Step 1 */}
            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                  <MessageSquare className="w-6 h-6 text-emerald-700" />
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-zinc-900 text-xl mb-2">1. Tell us what you need</h3>
                <p className="text-zinc-600 mb-4">
                  Start vague: "I need a prompt engineer." We'll ask smart follow-up questions to understand what you actually mean.
                </p>
                <div className="bg-zinc-50 rounded-xl p-4 text-sm text-zinc-600">
                  <p className="font-medium text-zinc-700 mb-2">We'll ask things like:</p>
                  <ul className="space-y-1">
                    <li>• What are you building?</li>
                    <li>• What would success look like by day 60?</li>
                    <li>• Any past hires that worked well—or didn't?</li>
                    <li>• Location/school preferences?</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                  <Search className="w-6 h-6 text-emerald-700" />
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-zinc-900 text-xl mb-2">2. We search deep</h3>
                <p className="text-zinc-600 mb-4">
                  Not just LinkedIn. We look at clubs, hackathons, GitHub activity, course signals, and our network to find people others miss.
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {searchSources.map((source, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-zinc-600 bg-zinc-50 rounded-lg px-3 py-2">
                      <source.icon className="w-4 h-4 text-zinc-400" />
                      <span>{source.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                  <Target className="w-6 h-6 text-emerald-700" />
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-zinc-900 text-xl mb-2">3. We tell you honestly what we know</h3>
                <p className="text-zinc-600 mb-4">
                  No fake "match scores." We show you: what we verified, what we observed, what's unknown, and what to ask them.
                </p>
                <div className="bg-zinc-50 rounded-xl p-4">
                  <div className="grid md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="font-medium text-emerald-700 mb-1">Known facts</p>
                      <p className="text-zinc-600">Verifiable: school, clubs, public projects</p>
                    </div>
                    <div>
                      <p className="font-medium text-blue-700 mb-1">Observed signals</p>
                      <p className="text-zinc-600">GitHub activity, hackathon wins, etc.</p>
                    </div>
                    <div>
                      <p className="font-medium text-amber-700 mb-1">Unknown</p>
                      <p className="text-zinc-600">What you'll need to verify in conversation</p>
                    </div>
                    <div>
                      <p className="font-medium text-zinc-700 mb-1">Why consider + next step</p>
                      <p className="text-zinc-600">Connection to your needs + what to ask</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 4 */}
            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                  <Users className="w-6 h-6 text-emerald-700" />
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-zinc-900 text-xl mb-2">4. You decide who to talk to</h3>
                <p className="text-zinc-600">
                  We're not evaluating if someone IS great—we're finding people worth a 30-minute conversation. You make the call.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section id="demo" className="py-24 px-6 bg-zinc-50 border-y border-zinc-100">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
              Try it yourself
            </h2>
            <p className="text-lg text-zinc-600">
              See how the conversation works.
            </p>
          </div>

          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-2xl border border-zinc-200 shadow-lg overflow-hidden">
              {/* Chat header */}
              <div className="bg-zinc-900 text-white px-6 py-4 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-cyan-400 flex items-center justify-center">
                  <Cpu className="w-5 h-5 text-zinc-900" />
                </div>
                <span className="font-semibold">Agencity</span>
              </div>

              {/* Chat body */}
              <div className="h-[400px] overflow-y-auto p-6 space-y-4">
                {!demoStarted ? (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <p className="text-zinc-500 mb-6">Tell us what role you're hiring for,<br />and we'll show you how it works.</p>
                    <Button
                      onClick={startDemo}
                      className="bg-emerald-600 text-white font-semibold px-6 py-3 rounded-full hover:bg-emerald-500 transition-colors"
                    >
                      Start Demo
                    </Button>
                  </div>
                ) : (
                  <>
                    {demoMessages.map((msg, i) => (
                      <div
                        key={i}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                            msg.role === "user"
                              ? "bg-emerald-600 text-white"
                              : "bg-zinc-100 text-zinc-900"
                          }`}
                        >
                          <p className="whitespace-pre-line text-sm">{msg.content}</p>
                        </div>
                      </div>
                    ))}

                    {isTyping && (
                      <div className="flex justify-start">
                        <div className="bg-zinc-100 rounded-2xl px-4 py-3">
                          <div className="flex gap-1">
                            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Search animation */}
                    {searchingStep > 0 && !showResults && (
                      <div className="bg-zinc-100 rounded-2xl p-4 space-y-2">
                        <p className="text-sm font-medium text-zinc-700 mb-3">Searching...</p>
                        {searchSources.map((source, i) => (
                          <div
                            key={i}
                            className={`flex items-center gap-2 text-sm transition-opacity duration-300 ${
                              i < searchingStep ? "opacity-100" : "opacity-30"
                            }`}
                          >
                            {i < searchingStep ? (
                              <Check className="w-4 h-4 text-emerald-600" />
                            ) : (
                              <Loader2 className="w-4 h-4 text-zinc-400 animate-spin" />
                            )}
                            <span className={i < searchingStep ? "text-zinc-700" : "text-zinc-400"}>
                              {source.name}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Options for initial question */}
                    {demoMessages.length === 1 && demoPath === "default" && !isTyping && (
                      <div className="flex flex-wrap gap-2">
                        {demoConversations.default[0].options?.map((option, i) => (
                          <button
                            key={i}
                            onClick={() => handleDemoOption(option)}
                            className="px-4 py-2 bg-white border border-zinc-200 rounded-full text-sm text-zinc-700 hover:bg-zinc-50 hover:border-zinc-300 transition-colors"
                          >
                            {option}
                          </button>
                        ))}
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              {/* Input area */}
              {demoStarted && !showResults && demoMessages.length > 1 && !isTyping && searchingStep === 0 && (
                <form onSubmit={handleDemoSubmit} className="border-t border-zinc-200 p-4 flex gap-3">
                  <input
                    type="text"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="Type your answer..."
                    className="flex-1 px-4 py-2 bg-zinc-50 border border-zinc-200 rounded-full text-sm focus:outline-none focus:border-emerald-400 transition-colors"
                  />
                  <button
                    type="submit"
                    className="w-10 h-10 bg-emerald-600 rounded-full flex items-center justify-center text-white hover:bg-emerald-500 transition-colors"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              )}

              {/* Results */}
              {showResults && (
                <div className="border-t border-zinc-200 p-4">
                  <p className="text-sm font-medium text-emerald-700 mb-2">Found 3 candidates worth talking to ↓</p>
                </div>
              )}
            </div>

            {/* Results cards */}
            <AnimatePresence>
              {showResults && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  className="mt-6 space-y-4"
                >
                  {sampleCandidates.map((candidate, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: i * 0.15 }}
                      className="bg-white rounded-2xl border border-zinc-200 p-5 shadow-sm"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h4 className="font-semibold text-zinc-900">{candidate.name}</h4>
                          <p className="text-sm text-zinc-500">{candidate.tagline}</p>
                        </div>
                        <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-1 rounded">
                          Worth a conversation
                        </span>
                      </div>

                      <div className="grid md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mb-2">Known Facts</p>
                          <ul className="space-y-1">
                            {candidate.knownFacts.map((fact, j) => (
                              <li key={j} className="text-sm text-zinc-600 flex items-start gap-1.5">
                                <Check className="w-3.5 h-3.5 text-emerald-600 mt-0.5 flex-shrink-0" />
                                {fact}
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-blue-700 uppercase tracking-wider mb-2">Observed Signals</p>
                          <ul className="space-y-1">
                            {candidate.observedSignals.map((signal, j) => (
                              <li key={j} className="text-sm text-zinc-600 flex items-start gap-1.5">
                                <span className="text-blue-500">•</span>
                                {signal}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      <div className="mb-4">
                        <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2">Unknown (verify in conversation)</p>
                        <ul className="space-y-1">
                          {candidate.unknown.map((item, j) => (
                            <li key={j} className="text-sm text-zinc-500 flex items-start gap-1.5">
                              <span className="text-amber-500">?</span>
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="bg-zinc-50 rounded-lg p-3 space-y-2">
                        <div>
                          <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Why consider</p>
                          <p className="text-sm text-zinc-700">{candidate.whyConsider}</p>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Suggested first step</p>
                          <p className="text-sm text-zinc-700">{candidate.nextStep}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}

                  <div className="text-center pt-4">
                    <Button
                      onClick={() => {
                        setDemoStarted(false);
                        setShowResults(false);
                        setDemoMessages([]);
                        setSearchingStep(0);
                        setDemoPath("default");
                        setDemoStep(0);
                      }}
                      variant="outline"
                      className="border-zinc-300 text-zinc-700"
                    >
                      Try again
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </section>

      {/* The Honest Approach Section */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
              We're honest about what we know.
            </h2>
            <p className="text-lg text-zinc-600 max-w-2xl mx-auto">
              Most people don't have rich public profiles. We don't pretend otherwise.
            </p>
          </div>

          <div className="max-w-3xl mx-auto">
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 md:p-8">
              <p className="text-zinc-700 mb-6 text-center">
                We're not evaluating if someone <em>is</em> a great prompt engineer.<br />
                We're finding people <strong>worth a 30-minute conversation</strong>.
              </p>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-red-50 border border-red-200 rounded-xl p-5">
                  <h4 className="font-semibold text-red-800 mb-3">We don't say:</h4>
                  <ul className="space-y-2 text-sm text-red-700">
                    <li>• "92% match score"</li>
                    <li>• "Strong prompt engineering skills"</li>
                    <li>• "Great culture fit"</li>
                    <li>• Claims we can't verify</li>
                  </ul>
                </div>
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5">
                  <h4 className="font-semibold text-emerald-800 mb-3">We do say:</h4>
                  <ul className="space-y-2 text-sm text-emerald-700">
                    <li>• "Has 2 LLM projects on GitHub"</li>
                    <li>• "Won hackathon with chatbot"</li>
                    <li>• "Skill level unknown—ask about X"</li>
                    <li>• Facts + signals + unknowns</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-24 px-6 bg-zinc-50 border-y border-zinc-100">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900 mb-4">
              FAQ
            </h2>
          </div>

          <div className="space-y-4">
            {[
              {
                q: "Where do candidates come from?",
                a: "Our 6,000+ opted-in network, plus deep searches across GitHub, university clubs, hackathons, and other signals. We'll tell you exactly where we found each person.",
              },
              {
                q: "How is this different from LinkedIn search?",
                a: "LinkedIn finds people with optimized profiles. We find people who could be great but aren't obviously visible—based on activity signals, not keywords.",
              },
              {
                q: "What if I don't know exactly what I need?",
                a: "That's the point. Start vague ('I need a prompt engineer') and we'll ask clarifying questions until we understand what you actually mean.",
              },
              {
                q: "How fast do I get candidates?",
                a: "Usually within 24-72 hours after we understand what you're looking for.",
              },
              {
                q: "What if the candidates aren't good?",
                a: "We show you why we surfaced each person. If our signals were wrong, tell us—we learn from your feedback and improve.",
              },
            ].map((item, i) => (
              <div
                key={i}
                className="bg-white rounded-xl border border-zinc-200 overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between p-5 text-left"
                >
                  <span className="font-medium text-zinc-900">{item.q}</span>
                  <ChevronDown
                    className={`w-5 h-5 text-zinc-400 transition-transform ${
                      openFaq === i ? "rotate-180" : ""
                    }`}
                  />
                </button>
                {openFaq === i && (
                  <div className="px-5 pb-5 pt-0">
                    <p className="text-zinc-600">{item.a}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section id="waitlist" className="py-24 px-6 bg-zinc-900 text-white">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
            Find the people you can't search for.
          </h2>
          <p className="text-zinc-400 mb-8">
            Tell us what you need. We'll find candidates worth talking to.
          </p>

          <form onSubmit={handleSubmitWaitlist} className="space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              className="w-full max-w-md px-5 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder:text-zinc-500 focus:border-emerald-400 focus:outline-none transition-colors"
            />
            <div>
              <Button
                type="submit"
                className="bg-emerald-600 text-white font-semibold px-8 py-4 rounded-xl hover:bg-emerald-500 transition-colors"
              >
                Request Access
              </Button>
            </div>
          </form>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-zinc-100 bg-white">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
              <Cpu className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-zinc-900">Agencity</span>
          </div>
          <p className="text-zinc-500 text-sm">
            © {new Date().getFullYear()} Agencity. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
