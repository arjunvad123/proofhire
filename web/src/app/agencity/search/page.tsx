"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Search,
  Users,
  Briefcase,
  MapPin,
  ExternalLink,
  Linkedin,
  ArrowLeft,
  Loader2,
  Building2,
  Zap
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api";

interface SearchResult {
  full_name: string;
  current_title: string;
  current_company: string;
  linkedin_url?: string;
  location?: string;
  match_score?: number;
  match_reasons?: string[];
}

export default function SearchPage() {
  const searchParams = useSearchParams();
  const companyId = searchParams.get("company");

  const [roleTitle, setRoleTitle] = useState("Software Engineer");
  const [skills, setSkills] = useState("TypeScript, Node.js, React");
  const [location, setLocation] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async () => {
    if (!companyId) return;

    setLoading(true);
    setHasSearched(true);

    try {
      const response = await fetch(
        `${API_URL}/v2/search/network/${companyId}?role_title=${encodeURIComponent(
          roleTitle
        )}&skills=${encodeURIComponent(skills)}&location=${encodeURIComponent(
          location
        )}&limit=20`
      );

      if (response.ok) {
        const data = await response.json();
        setResults(data.candidates || []);
      } else {
        console.error("Search failed:", response.statusText);
        setResults([]);
      }
    } catch (error) {
      console.error("Search error:", error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

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
                <h1 className="text-xl font-bold text-slate-900">Network Search</h1>
                <p className="text-sm text-slate-500">Find candidates in your connections</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-medium text-slate-600">
                Searching {companyId === "100b5ac1-1912-4970-a378-04d0169fd597" ? "3,637" : "0"} connections
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Search Form */}
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Role Title
              </label>
              <div className="relative">
                <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={roleTitle}
                  onChange={(e) => setRoleTitle(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Software Engineer"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Required Skills
              </label>
              <input
                type="text"
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., TypeScript, React"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Location (Optional)
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., San Francisco"
                />
              </div>
            </div>
          </div>

          <button
            onClick={handleSearch}
            disabled={loading || !roleTitle}
            className="w-full md:w-auto px-8 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-300 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Search Network
              </>
            )}
          </button>
        </div>

        {/* Results */}
        {loading && (
          <div className="text-center py-12">
            <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
            <p className="text-slate-600">Searching your network...</p>
          </div>
        )}

        {!loading && hasSearched && results.length === 0 && (
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">No matches found</h3>
            <p className="text-slate-600">Try adjusting your search criteria</p>
          </div>
        )}

        {!loading && results.length > 0 && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-slate-900">
                Found {results.length} candidate{results.length !== 1 ? "s" : ""}
              </h2>
              <p className="text-sm text-slate-500">Direct connections from your network</p>
            </div>

            <div className="space-y-4">
              {results.map((result, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-slate-900">
                          {result.full_name}
                        </h3>
                        {result.match_score && result.match_score > 0 && (
                          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">
                            {result.match_score}% match
                          </span>
                        )}
                      </div>

                      <div className="space-y-1 mb-3">
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <Briefcase className="w-4 h-4" />
                          <span>
                            {result.current_title || "Unknown Title"}
                            {result.current_company && ` @ ${result.current_company}`}
                          </span>
                        </div>

                        {result.location && (
                          <div className="flex items-center gap-2 text-sm text-slate-600">
                            <MapPin className="w-4 h-4" />
                            <span>{result.location}</span>
                          </div>
                        )}
                      </div>

                      {result.match_reasons && result.match_reasons.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-3">
                          {result.match_reasons.slice(0, 3).map((reason, idx) => (
                            <span
                              key={idx}
                              className="px-3 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-full"
                            >
                              {reason}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {result.linkedin_url && (
                      <a
                        href={result.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 hover:bg-slate-100 rounded-lg transition-colors group"
                      >
                        <Linkedin className="w-5 h-5 text-blue-600 group-hover:text-blue-700" />
                      </a>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Demo Notice */}
        {companyId === "100b5ac1-1912-4970-a378-04d0169fd597" && !hasSearched && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mt-6">
            <div className="flex items-start gap-3">
              <Zap className="w-5 h-5 text-amber-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-amber-900 mb-1">
                  Ready to Search Confido's Network
                </h3>
                <p className="text-sm text-amber-800 mb-3">
                  You have 3,637 LinkedIn connections imported. Click "Search Network" above to find candidates matching your criteria.
                </p>
                <p className="text-xs text-amber-700">
                  <strong>Tip:</strong> The search uses intelligent matching based on job titles, skills, and experience to find the best candidates in your network.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
