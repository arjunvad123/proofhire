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
  ArrowLeft,
  RefreshCw,
  MapPin,
  GraduationCap,
  ExternalLink
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

export default function AgencityDemoPage() {
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
  };

  const examplePrompts = [
    "I need a prompt engineer for my AI startup",
    "Looking for a backend engineer who knows Python and FastAPI",
    "Need someone for ML/AI research, preferably from Waterloo",
  ];

  return (
    <div className="min-h-screen bg-white text-zinc-900">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-zinc-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/agencity" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
                <Cpu className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-zinc-900">Agencity</span>
            </Link>
            <span className="text-xs bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full font-medium">
              Live Demo
            </span>
          </div>

          <button
            onClick={resetConversation}
            className="flex items-center gap-2 text-sm text-zinc-500 hover:text-zinc-900 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Reset
          </button>
        </div>
      </header>

      <div className="pt-20 pb-8 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Title section */}
          <div className="text-center py-8">
            <h1 className="text-3xl font-bold text-zinc-900 mb-2">
              Find the people you can't search for
            </h1>
            <p className="text-zinc-600">
              Tell us what you need. We'll search our network of 1,375+ candidates and tell you honestly what we know.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Chat Panel */}
            <div className="bg-white rounded-2xl border border-zinc-200 shadow-sm flex flex-col h-[600px]">
              {/* Chat header */}
              <div className="bg-zinc-900 text-white px-6 py-4 rounded-t-2xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-cyan-400 flex items-center justify-center">
                    <Cpu className="w-5 h-5 text-zinc-900" />
                  </div>
                  <span className="font-semibold">Agencity Agent</span>
                </div>
                <div className="text-xs text-zinc-400">
                  {status === "idle" ? "Ready" :
                   status === "in_progress" ? "Gathering context..." :
                   status === "complete" ? "Search complete" : status}
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <div className="w-16 h-16 rounded-2xl bg-emerald-50 flex items-center justify-center mb-4">
                      <Sparkles className="w-8 h-8 text-emerald-600" />
                    </div>
                    <p className="text-zinc-500 mb-6">Tell me what role you're hiring for,<br />and I'll find candidates worth talking to.</p>
                    <div className="space-y-2 w-full max-w-sm">
                      {examplePrompts.map((example) => (
                        <button
                          key={example}
                          onClick={() => setInput(example)}
                          className="block w-full text-left px-4 py-3 bg-zinc-50 hover:bg-zinc-100 rounded-xl text-sm text-zinc-700 transition-colors border border-zinc-100"
                        >
                          "{example}"
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
                      <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                        <Bot className="w-4 h-4 text-emerald-700" />
                      </div>
                    )}
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                        msg.role === "user"
                          ? "bg-emerald-600 text-white"
                          : "bg-zinc-100 text-zinc-900"
                      }`}
                    >
                      <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                    </div>
                    {msg.role === "user" && (
                      <div className="w-8 h-8 rounded-full bg-zinc-200 flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-zinc-600" />
                      </div>
                    )}
                  </motion.div>
                ))}

                {isLoading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center">
                      <Loader2 className="w-4 h-4 text-emerald-700 animate-spin" />
                    </div>
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
                {isSearching && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-zinc-50 rounded-2xl p-5 border border-zinc-100"
                  >
                    <p className="text-sm font-medium text-zinc-700 mb-4 flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
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
                            <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                          ) : (
                            <Loader2 className="w-4 h-4 text-zinc-300 animate-spin flex-shrink-0" />
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
              <form onSubmit={handleSubmit} className="p-4 border-t border-zinc-100">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Describe what you're looking for..."
                    className="flex-1 px-4 py-3 bg-zinc-50 border border-zinc-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    disabled={isLoading || isSearching}
                  />
                  <button
                    type="submit"
                    disabled={isLoading || isSearching || !input.trim()}
                    className="w-12 h-12 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl flex items-center justify-center text-white transition-colors"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </form>
            </div>

            {/* Results Panel */}
            <div className="bg-white rounded-2xl border border-zinc-200 shadow-sm flex flex-col h-[600px]">
              <div className="px-6 py-4 border-b border-zinc-100 flex items-center justify-between">
                <div>
                  <h2 className="font-semibold text-zinc-900">
                    {showCandidates ? `Candidates (${candidates.length})` : "Results"}
                  </h2>
                  <p className="text-xs text-zinc-500">
                    {showCandidates ? "Worth a conversation" : "Candidates will appear here"}
                  </p>
                </div>
                {blueprint && (
                  <div className="text-right">
                    <p className="text-xs text-zinc-500">Searching for</p>
                    <p className="text-sm font-medium text-emerald-700">{blueprint.role_title}</p>
                  </div>
                )}
              </div>

              <div className="flex-1 overflow-y-auto p-4">
                {!showCandidates ? (
                  <div className="flex flex-col items-center justify-center h-full text-center px-6">
                    <div className="w-16 h-16 rounded-2xl bg-zinc-50 flex items-center justify-center mb-4">
                      <Users className="w-8 h-8 text-zinc-300" />
                    </div>
                    <p className="text-zinc-400">
                      Start a conversation to find candidates from our network.
                    </p>
                  </div>
                ) : candidates.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center px-6">
                    <p className="text-zinc-400">No candidates found matching your criteria.</p>
                  </div>
                ) : (
                  <AnimatePresence>
                    <div className="space-y-4">
                      {candidates.map((candidate, i) => (
                        <motion.div
                          key={candidate.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.4, delay: i * 0.1 }}
                          className="bg-white rounded-2xl border border-zinc-200 p-5 hover:border-zinc-300 hover:shadow-sm transition-all"
                        >
                          {/* Header */}
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <h3 className="font-semibold text-zinc-900 text-lg">{candidate.name}</h3>
                              <p className="text-sm text-zinc-500">{candidate.tagline}</p>
                            </div>
                            <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
                              Worth a chat
                            </span>
                          </div>

                          {/* Meta info */}
                          <div className="flex flex-wrap gap-3 mb-4">
                            {candidate.school && (
                              <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                                <GraduationCap className="w-3.5 h-3.5" />
                                {candidate.school}
                              </div>
                            )}
                            {candidate.github_username && (
                              <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                                <Github className="w-3.5 h-3.5" />
                                @{candidate.github_username}
                              </div>
                            )}
                            {candidate.location && (
                              <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                                <MapPin className="w-3.5 h-3.5" />
                                {candidate.location}
                              </div>
                            )}
                          </div>

                          {/* Known Facts */}
                          {candidate.known_facts.length > 0 && (
                            <div className="mb-3">
                              <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mb-2">
                                Known Facts
                              </p>
                              <ul className="space-y-1">
                                {candidate.known_facts.slice(0, 3).map((fact, j) => (
                                  <li key={j} className="text-sm text-zinc-600 flex items-start gap-2">
                                    <Check className="w-3.5 h-3.5 text-emerald-600 mt-0.5 flex-shrink-0" />
                                    {fact}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Observed Signals */}
                          {candidate.observed_signals.length > 0 && (
                            <div className="mb-3">
                              <p className="text-xs font-semibold text-blue-700 uppercase tracking-wider mb-2">
                                Observed Signals
                              </p>
                              <ul className="space-y-1">
                                {candidate.observed_signals.slice(0, 3).map((signal, j) => (
                                  <li key={j} className="text-sm text-zinc-600 flex items-start gap-2">
                                    <span className="text-blue-500 mt-0.5">•</span>
                                    {signal}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Unknown */}
                          {candidate.unknown.length > 0 && (
                            <div className="mb-4">
                              <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2">
                                Unknown (verify in conversation)
                              </p>
                              <ul className="space-y-1">
                                {candidate.unknown.slice(0, 2).map((item, j) => (
                                  <li key={j} className="text-sm text-zinc-500 flex items-start gap-2">
                                    <span className="text-amber-500 mt-0.5">?</span>
                                    {item}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Why Consider & Next Step */}
                          <div className="bg-zinc-50 rounded-xl p-4 space-y-3">
                            {candidate.why_consider && (
                              <div>
                                <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">
                                  Why consider
                                </p>
                                <p className="text-sm text-zinc-700">{candidate.why_consider}</p>
                              </div>
                            )}
                            {candidate.next_step && (
                              <div>
                                <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">
                                  Suggested first step
                                </p>
                                <p className="text-sm text-zinc-700">{candidate.next_step}</p>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </AnimatePresence>
                )}
              </div>

              {/* Blueprint Preview */}
              {blueprint && (
                <div className="px-4 py-3 border-t border-zinc-100 bg-zinc-50 rounded-b-2xl">
                  <div className="flex items-center gap-4 text-xs text-zinc-600">
                    <div>
                      <span className="text-zinc-400">Role:</span>{" "}
                      <span className="font-medium">{blueprint.role_title}</span>
                    </div>
                    {blueprint.location_preferences.length > 0 && (
                      <div>
                        <span className="text-zinc-400">Location:</span>{" "}
                        <span className="font-medium">{blueprint.location_preferences.join(", ")}</span>
                      </div>
                    )}
                    {blueprint.must_haves.length > 0 && (
                      <div>
                        <span className="text-zinc-400">Must-haves:</span>{" "}
                        <span className="font-medium">{blueprint.must_haves.slice(0, 2).join(", ")}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer note */}
          <div className="text-center mt-8">
            <p className="text-sm text-zinc-400">
              Searching 1,375+ real candidates from our Supabase database •
              <span className="text-emerald-600 ml-1">Live data</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
