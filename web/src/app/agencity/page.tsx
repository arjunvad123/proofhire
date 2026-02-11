"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  Send,
  Loader2,
  Bot,
  User,
  Cpu,
  Check,
  Users,
  Github,
  BookOpen,
  Trophy,
  Sparkles,
  RefreshCw,
  MapPin,
  GraduationCap,
  ExternalLink,
  ArrowRight,
  ChevronDown
} from "lucide-react";

const API_URL = "http://localhost:8001";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Candidate {
  id: string;
  name: string;
  tagline: string;
  known_facts: string[];
  observed_signals: string[];
  unknown: string[];
  why_consider: string;
  next_step: string;
  github_username?: string;
  school?: string;
  location?: string;
}

interface Blueprint {
  role_title: string;
  company_context: string;
  specific_work: string;
  success_criteria: string;
  must_haves: string[];
  nice_to_haves: string[];
  location_preferences: string[];
}

const searchSources = [
  { name: "Our network (1,375+)", icon: Users, color: "text-emerald-600" },
  { name: "GitHub activity", icon: Github, color: "text-zinc-700" },
  { name: "Devpost hackathons", icon: Trophy, color: "text-amber-600" },
  { name: "Codeforces rankings", icon: Sparkles, color: "text-blue-600" },
  { name: "Stack Overflow", icon: BookOpen, color: "text-orange-600" },
  { name: "HackerNews", icon: ExternalLink, color: "text-red-600" },
];

export default function AgencityPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [blueprint, setBlueprint] = useState<Blueprint | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [showCandidates, setShowCandidates] = useState(false);
  const [searchingStep, setSearchingStep] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const [expandedCandidate, setExpandedCandidate] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, searchingStep]);

  const startConversation = async (message: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/conversations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "demo-user",
          initial_message: message,
        }),
      });
      const data = await res.json();
      setConversationId(data.id);
      setStatus(data.status);
      setMessages((prev) => [
        ...prev,
        { role: "user", content: message },
        { role: "assistant", content: data.message },
      ]);
      if (data.blueprint) {
        setBlueprint(data.blueprint);
        await runSearch(data.blueprint);
      }
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Unable to connect to the server. Make sure the backend is running on port 8001." },
      ]);
    }
    setIsLoading(false);
  };

  const sendMessage = async (message: string) => {
    if (!conversationId) {
      await startConversation(message);
      return;
    }

    setIsLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: message }]);

    try {
      const res = await fetch(`${API_URL}/api/conversations/${conversationId}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: message }),
      });
      const data = await res.json();
      setStatus(data.status);
      setMessages((prev) => [...prev, { role: "assistant", content: data.message }]);
      if (data.blueprint) {
        setBlueprint(data.blueprint);
        await runSearch(data.blueprint);
      }
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error sending message. Please try again." },
      ]);
    }
    setIsLoading(false);
  };

  const runSearch = async (bp: Blueprint) => {
    setIsSearching(true);
    setSearchingStep(0);

    // Animate through search steps
    for (let i = 1; i <= searchSources.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 400));
      setSearchingStep(i);
    }

    // Actually search
    try {
      const res = await fetch(`${API_URL}/api/shortlists/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ blueprint: bp }),
      });
      const data = await res.json();
      setCandidates(data.candidates || []);

      await new Promise(resolve => setTimeout(resolve, 500));
      setShowCandidates(true);
    } catch (error) {
      console.error("Search error:", error);
    }

    setIsSearching(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const message = input.trim();
    setInput("");
    sendMessage(message);
  };

  const resetConversation = () => {
    setMessages([]);
    setConversationId(null);
    setStatus("idle");
    setBlueprint(null);
    setCandidates([]);
    setShowCandidates(false);
    setSearchingStep(0);
    setIsSearching(false);
    setExpandedCandidate(null);
  };

  const examplePrompts = [
    "I need a prompt engineer for my AI startup",
    "Looking for a backend engineer who knows Python",
    "Need someone for ML/AI work at Waterloo",
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-50 to-white text-zinc-900">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-zinc-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Cpu className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-zinc-900">Agencity</span>
            </Link>
            <span className="text-xs bg-emerald-100 text-emerald-700 px-3 py-1.5 rounded-full font-semibold">
              Live Demo
            </span>
          </div>

          <button
            onClick={resetConversation}
            className="flex items-center gap-2 text-sm text-zinc-500 hover:text-zinc-900 transition-colors px-3 py-2 rounded-lg hover:bg-zinc-100"
          >
            <RefreshCw className="w-4 h-4" />
            Start Over
          </button>
        </div>
      </header>

      <main className="pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Hero */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-10"
          >
            <h1 className="text-4xl md:text-5xl font-bold text-zinc-900 mb-4 tracking-tight">
              Find the people{" "}
              <span className="text-emerald-600">you can't search for</span>
            </h1>
            <p className="text-lg text-zinc-600 max-w-2xl mx-auto">
              Tell us what you need—even if it's vague. We'll search 1,375+ candidates
              and tell you honestly what we know vs. what you'll need to verify.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
            {/* Chat Panel - 2 columns */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="lg:col-span-2 bg-white rounded-3xl border border-zinc-200 shadow-xl shadow-zinc-200/50 flex flex-col h-[650px] overflow-hidden"
            >
              {/* Chat header */}
              <div className="bg-gradient-to-r from-zinc-900 to-zinc-800 text-white px-6 py-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-400 flex items-center justify-center">
                    <Cpu className="w-5 h-5 text-zinc-900" />
                  </div>
                  <div>
                    <span className="font-semibold block">Agencity Agent</span>
                    <span className="text-xs text-zinc-400">
                      {status === "idle" ? "Ready to help" :
                       status === "in_progress" ? "Gathering context..." :
                       status === "complete" ? "Search complete" : status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-zinc-50/50">
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-emerald-100 to-cyan-100 flex items-center justify-center mb-6">
                      <Sparkles className="w-10 h-10 text-emerald-600" />
                    </div>
                    <p className="text-zinc-600 mb-6 text-lg">What role are you hiring for?</p>
                    <div className="space-y-3 w-full">
                      {examplePrompts.map((example) => (
                        <button
                          key={example}
                          onClick={() => setInput(example)}
                          className="block w-full text-left px-5 py-4 bg-white hover:bg-emerald-50 rounded-2xl text-sm text-zinc-700 transition-all border border-zinc-200 hover:border-emerald-300 hover:shadow-md"
                        >
                          <span className="text-zinc-400 mr-2">"</span>
                          {example}
                          <span className="text-zinc-400 ml-1">"</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {messages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
                  >
                    {msg.role === "assistant" && (
                      <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-100 to-emerald-200 flex items-center justify-center flex-shrink-0">
                        <Bot className="w-5 h-5 text-emerald-700" />
                      </div>
                    )}
                    <div
                      className={`max-w-[85%] rounded-2xl px-5 py-3 ${
                        msg.role === "user"
                          ? "bg-gradient-to-r from-emerald-600 to-emerald-500 text-white shadow-lg shadow-emerald-500/20"
                          : "bg-white text-zinc-900 border border-zinc-200 shadow-sm"
                      }`}
                    >
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                    </div>
                    {msg.role === "user" && (
                      <div className="w-9 h-9 rounded-xl bg-zinc-200 flex items-center justify-center flex-shrink-0">
                        <User className="w-5 h-5 text-zinc-600" />
                      </div>
                    )}
                  </motion.div>
                ))}

                {isLoading && (
                  <div className="flex gap-3">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-100 to-emerald-200 flex items-center justify-center">
                      <Loader2 className="w-5 h-5 text-emerald-700 animate-spin" />
                    </div>
                    <div className="bg-white rounded-2xl px-5 py-4 border border-zinc-200 shadow-sm">
                      <div className="flex gap-1.5">
                        <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                        <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                        <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                      </div>
                    </div>
                  </div>
                )}

                {/* Search animation */}
                {isSearching && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-2xl p-6 border border-zinc-200 shadow-sm"
                  >
                    <p className="text-sm font-semibold text-zinc-700 mb-4 flex items-center gap-2">
                      <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                      Searching across sources...
                    </p>
                    <div className="space-y-3">
                      {searchSources.map((source, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0.3 }}
                          animate={{ opacity: i < searchingStep ? 1 : 0.3 }}
                          className="flex items-center gap-3 text-sm"
                        >
                          {i < searchingStep ? (
                            <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center">
                              <Check className="w-3 h-3 text-emerald-600" />
                            </div>
                          ) : (
                            <Loader2 className="w-5 h-5 text-zinc-300 animate-spin" />
                          )}
                          <source.icon className={`w-4 h-4 ${i < searchingStep ? source.color : "text-zinc-300"}`} />
                          <span className={i < searchingStep ? "text-zinc-700" : "text-zinc-400"}>
                            {source.name}
                          </span>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <form onSubmit={handleSubmit} className="p-4 border-t border-zinc-100 bg-white">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Describe what you're looking for..."
                    className="flex-1 px-5 py-4 bg-zinc-50 border border-zinc-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    disabled={isLoading || isSearching}
                  />
                  <button
                    type="submit"
                    disabled={isLoading || isSearching || !input.trim()}
                    className="w-14 h-14 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl flex items-center justify-center text-white transition-all shadow-lg shadow-emerald-500/20"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </form>
            </motion.div>

            {/* Results Panel - 3 columns */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="lg:col-span-3 bg-white rounded-3xl border border-zinc-200 shadow-xl shadow-zinc-200/50 flex flex-col h-[650px] overflow-hidden"
            >
              <div className="px-6 py-5 border-b border-zinc-100 flex items-center justify-between bg-gradient-to-r from-zinc-50 to-white">
                <div>
                  <h2 className="font-bold text-zinc-900 text-lg">
                    {showCandidates ? `Candidates Found (${candidates.length})` : "Candidate Results"}
                  </h2>
                  <p className="text-sm text-zinc-500">
                    {showCandidates ? "People worth a 30-minute conversation" : "Real candidates from our database"}
                  </p>
                </div>
                {blueprint && (
                  <div className="text-right bg-emerald-50 px-4 py-2 rounded-xl">
                    <p className="text-xs text-emerald-600 font-medium">Searching for</p>
                    <p className="text-sm font-bold text-emerald-700">{blueprint.role_title}</p>
                  </div>
                )}
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                {!showCandidates ? (
                  <div className="flex flex-col items-center justify-center h-full text-center px-6">
                    <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-zinc-100 to-zinc-50 flex items-center justify-center mb-6">
                      <Users className="w-12 h-12 text-zinc-300" />
                    </div>
                    <h3 className="text-xl font-semibold text-zinc-400 mb-2">No candidates yet</h3>
                    <p className="text-zinc-400 max-w-sm">
                      Start a conversation to search our network of 1,375+ real candidates.
                    </p>
                  </div>
                ) : candidates.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center px-6">
                    <p className="text-zinc-400">No candidates found matching your criteria.</p>
                  </div>
                ) : (
                  <AnimatePresence>
                    <div className="space-y-5">
                      {candidates.map((candidate, i) => (
                        <motion.div
                          key={candidate.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.4, delay: i * 0.1 }}
                          className="bg-white rounded-2xl border border-zinc-200 overflow-hidden hover:border-emerald-300 hover:shadow-lg transition-all"
                        >
                          {/* Candidate Header */}
                          <div
                            className="p-5 cursor-pointer"
                            onClick={() => setExpandedCandidate(
                              expandedCandidate === candidate.id ? null : candidate.id
                            )}
                          >
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                  <h3 className="font-bold text-zinc-900 text-lg">{candidate.name}</h3>
                                  <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
                                    Worth a chat
                                  </span>
                                </div>
                                <p className="text-sm text-zinc-500 mb-3">{candidate.tagline}</p>

                                {/* Meta info */}
                                <div className="flex flex-wrap gap-4">
                                  {candidate.school && (
                                    <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                                      <GraduationCap className="w-4 h-4 text-zinc-400" />
                                      {candidate.school}
                                    </div>
                                  )}
                                  {candidate.github_username && (
                                    <a
                                      href={`https://github.com/${candidate.github_username}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-900 transition-colors"
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      <Github className="w-4 h-4" />
                                      @{candidate.github_username}
                                      <ExternalLink className="w-3 h-3" />
                                    </a>
                                  )}
                                  {candidate.location && (
                                    <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                                      <MapPin className="w-4 h-4 text-zinc-400" />
                                      {candidate.location}
                                    </div>
                                  )}
                                </div>
                              </div>
                              <ChevronDown
                                className={`w-5 h-5 text-zinc-400 transition-transform ${
                                  expandedCandidate === candidate.id ? "rotate-180" : ""
                                }`}
                              />
                            </div>
                          </div>

                          {/* Expanded Content */}
                          <AnimatePresence>
                            {expandedCandidate === candidate.id && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.3 }}
                                className="border-t border-zinc-100"
                              >
                                <div className="p-5 space-y-5">
                                  <div className="grid md:grid-cols-2 gap-5">
                                    {/* Known Facts */}
                                    {candidate.known_facts.length > 0 && (
                                      <div className="bg-emerald-50/50 rounded-xl p-4">
                                        <p className="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                                          <Check className="w-4 h-4" />
                                          Known Facts
                                        </p>
                                        <ul className="space-y-2">
                                          {candidate.known_facts.map((fact, j) => (
                                            <li key={j} className="text-sm text-zinc-700 flex items-start gap-2">
                                              <Check className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                                              {fact}
                                            </li>
                                          ))}
                                        </ul>
                                      </div>
                                    )}

                                    {/* Observed Signals */}
                                    {candidate.observed_signals.length > 0 && (
                                      <div className="bg-blue-50/50 rounded-xl p-4">
                                        <p className="text-xs font-bold text-blue-700 uppercase tracking-wider mb-3">
                                          Observed Signals
                                        </p>
                                        <ul className="space-y-2">
                                          {candidate.observed_signals.map((signal, j) => (
                                            <li key={j} className="text-sm text-zinc-700 flex items-start gap-2">
                                              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2 flex-shrink-0" />
                                              {signal}
                                            </li>
                                          ))}
                                        </ul>
                                      </div>
                                    )}
                                  </div>

                                  {/* Unknown */}
                                  {candidate.unknown.length > 0 && (
                                    <div className="bg-amber-50/50 rounded-xl p-4">
                                      <p className="text-xs font-bold text-amber-700 uppercase tracking-wider mb-3">
                                        Unknown (verify in conversation)
                                      </p>
                                      <ul className="space-y-2">
                                        {candidate.unknown.map((item, j) => (
                                          <li key={j} className="text-sm text-zinc-600 flex items-start gap-2">
                                            <span className="text-amber-500 font-bold">?</span>
                                            {item}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {/* Why Consider & Next Step */}
                                  <div className="bg-gradient-to-r from-zinc-50 to-zinc-100/50 rounded-xl p-5 space-y-4">
                                    {candidate.why_consider && (
                                      <div>
                                        <p className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1">
                                          Why consider
                                        </p>
                                        <p className="text-sm text-zinc-800 font-medium">{candidate.why_consider}</p>
                                      </div>
                                    )}
                                    {candidate.next_step && (
                                      <div>
                                        <p className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1">
                                          Suggested first step
                                        </p>
                                        <p className="text-sm text-zinc-800">{candidate.next_step}</p>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </motion.div>
                      ))}
                    </div>
                  </AnimatePresence>
                )}
              </div>

              {/* Blueprint Preview */}
              {blueprint && (
                <div className="px-5 py-4 border-t border-zinc-100 bg-gradient-to-r from-zinc-50 to-white">
                  <div className="flex items-center gap-6 text-sm text-zinc-600">
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-400 text-xs">Role:</span>
                      <span className="font-semibold text-zinc-700">{blueprint.role_title}</span>
                    </div>
                    {blueprint.location_preferences.length > 0 && (
                      <div className="flex items-center gap-2">
                        <MapPin className="w-3.5 h-3.5 text-zinc-400" />
                        <span className="font-medium">{blueprint.location_preferences.join(", ")}</span>
                      </div>
                    )}
                    {blueprint.must_haves.length > 0 && (
                      <div className="hidden md:flex items-center gap-2">
                        <span className="text-zinc-400 text-xs">Must-haves:</span>
                        <span className="font-medium">{blueprint.must_haves.slice(0, 3).join(", ")}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          </div>

          {/* Footer */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="text-center mt-10"
          >
            <p className="text-sm text-zinc-400">
              Searching <span className="text-emerald-600 font-semibold">1,375+</span> real candidates from our Supabase database
            </p>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
