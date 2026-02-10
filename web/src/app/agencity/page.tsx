"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, User, Bot, Sparkles } from "lucide-react";

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

export default function AgencityTestPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [blueprint, setBlueprint] = useState<Blueprint | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [showCandidates, setShowCandidates] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const startConversation = async (message: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/conversations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "test-user",
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
        await searchCandidates(data.blueprint);
      }
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error connecting to server. Is the backend running?" },
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
        await searchCandidates(data.blueprint);
      }
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error sending message." },
      ]);
    }
    setIsLoading(false);
  };

  const searchCandidates = async (bp: Blueprint) => {
    try {
      const res = await fetch(`${API_URL}/api/shortlists/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ blueprint: bp }),
      });
      const data = await res.json();
      setCandidates(data.candidates || []);
      setShowCandidates(true);
    } catch (error) {
      console.error("Search error:", error);
    }
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
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-white">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-blue-400" />
            <span className="text-xl font-bold">Agencity</span>
            <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full">
              Test Mode
            </span>
          </div>
          <button
            onClick={resetConversation}
            className="text-sm text-slate-400 hover:text-white transition"
          >
            Reset
          </button>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Chat Panel */}
          <div className="bg-slate-800/50 rounded-xl border border-slate-700 flex flex-col h-[600px]">
            <div className="p-4 border-b border-slate-700">
              <h2 className="font-semibold">Conversation</h2>
              <p className="text-sm text-slate-400">
                {status === "idle" ? "Start by describing what you're looking for" :
                 status === "in_progress" ? "Gathering context..." :
                 status === "complete" ? "Search complete!" : status}
              </p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center text-slate-400 py-8">
                  <p className="mb-4">Try something like:</p>
                  <div className="space-y-2">
                    {[
                      "I need a prompt engineer for my AI startup",
                      "Looking for a backend engineer who knows Python",
                      "Need someone for ML/AI work at UCSD",
                    ].map((example) => (
                      <button
                        key={example}
                        onClick={() => {
                          setInput(example);
                        }}
                        className="block w-full text-left px-4 py-2 bg-slate-700/50 hover:bg-slate-700 rounded-lg text-sm transition"
                      >
                        "{example}"
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
                >
                  {msg.role === "assistant" && (
                    <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-blue-400" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-xl px-4 py-2 ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-slate-700 text-slate-100"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                  </div>
                  <div className="bg-slate-700 rounded-xl px-4 py-2">
                    <p className="text-slate-400">Thinking...</p>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-slate-700">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Describe what you're looking for..."
                  className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg px-4 py-2 transition"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </form>
          </div>

          {/* Results Panel */}
          <div className="bg-slate-800/50 rounded-xl border border-slate-700 flex flex-col h-[600px]">
            <div className="p-4 border-b border-slate-700">
              <h2 className="font-semibold">
                {showCandidates ? `Candidates (${candidates.length})` : "Results"}
              </h2>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {!showCandidates ? (
                <div className="text-center text-slate-400 py-8">
                  <p>Candidates will appear here after the search completes.</p>
                </div>
              ) : candidates.length === 0 ? (
                <div className="text-center text-slate-400 py-8">
                  <p>No candidates found matching your criteria.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {candidates.map((candidate) => (
                    <div
                      key={candidate.id}
                      className="bg-slate-700/50 rounded-xl p-4 border border-slate-600"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="font-semibold text-lg">{candidate.name}</h3>
                          <p className="text-sm text-slate-400">{candidate.tagline}</p>
                        </div>
                      </div>

                      {/* Known Facts */}
                      {candidate.known_facts.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-xs font-medium text-green-400 uppercase tracking-wide mb-1">
                            Known Facts
                          </h4>
                          <ul className="text-sm text-slate-300 space-y-0.5">
                            {candidate.known_facts.map((fact, i) => (
                              <li key={i}>• {fact}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Observed Signals */}
                      {candidate.observed_signals.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-xs font-medium text-blue-400 uppercase tracking-wide mb-1">
                            Observed Signals
                          </h4>
                          <ul className="text-sm text-slate-300 space-y-0.5">
                            {candidate.observed_signals.map((signal, i) => (
                              <li key={i}>• {signal}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Unknown */}
                      {candidate.unknown.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-xs font-medium text-amber-400 uppercase tracking-wide mb-1">
                            Unknown (Verify in conversation)
                          </h4>
                          <ul className="text-sm text-slate-400 space-y-0.5">
                            {candidate.unknown.map((item, i) => (
                              <li key={i}>• {item}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Why Consider */}
                      {candidate.why_consider && (
                        <div className="mb-3">
                          <h4 className="text-xs font-medium text-purple-400 uppercase tracking-wide mb-1">
                            Why Consider
                          </h4>
                          <p className="text-sm text-slate-300">{candidate.why_consider}</p>
                        </div>
                      )}

                      {/* Next Step */}
                      {candidate.next_step && (
                        <div className="bg-slate-600/50 rounded-lg p-3">
                          <h4 className="text-xs font-medium text-slate-300 uppercase tracking-wide mb-1">
                            Suggested Next Step
                          </h4>
                          <p className="text-sm text-white">{candidate.next_step}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Blueprint Preview */}
            {blueprint && (
              <div className="p-4 border-t border-slate-700 bg-slate-900/50">
                <h4 className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">
                  Role Blueprint
                </h4>
                <div className="text-sm space-y-1">
                  <p>
                    <span className="text-slate-400">Role:</span> {blueprint.role_title}
                  </p>
                  <p>
                    <span className="text-slate-400">Work:</span> {blueprint.specific_work}
                  </p>
                  {blueprint.location_preferences.length > 0 && (
                    <p>
                      <span className="text-slate-400">Location:</span>{" "}
                      {blueprint.location_preferences.join(", ")}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
