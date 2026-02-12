"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  Building2,
  Users,
  Briefcase,
  Search,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Linkedin,
  Database,
  Zap,
  BarChart3
} from "lucide-react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api";

interface CompanyStats {
  name: string;
  people_count: number;
  roles_count: number;
  linkedin_imported: boolean;
  existing_db_imported: boolean;
}

// Demo data for quick loading
const DEMO_DATA = {
  greptile: {
    name: "Greptile",
    people_count: 0,
    roles_count: 1,
    linkedin_imported: false,
    existing_db_imported: false,
    role: {
      title: "Software Engineer (Generalist)",
      required_skills: ["TypeScript", "Node.js", "AWS", "Lambda", "Postgres", "NextJS"],
    },
  },
  "100b5ac1-1912-4970-a378-04d0169fd597": {
    name: "Confido",
    people_count: 3637,
    roles_count: 4,
    linkedin_imported: true,
    existing_db_imported: true,
    roles: [
      "Software Engineer",
      "Senior Sales Development Representative",
      "Head of Finance",
      "Founding Growth"
    ],
  },
};

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const companyId = searchParams.get("company");

  const [companyStats, setCompanyStats] = useState<CompanyStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load demo data immediately
    if (companyId && DEMO_DATA[companyId as keyof typeof DEMO_DATA]) {
      const demoData = DEMO_DATA[companyId as keyof typeof DEMO_DATA];
      setCompanyStats(demoData);
      setLoading(false);
    } else {
      // Fall back to API call
      fetchCompanyStats();
    }
  }, [companyId]);

  const fetchCompanyStats = async () => {
    if (!companyId) {
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/companies/${companyId}`);
      if (response.ok) {
        const data = await response.json();
        setCompanyStats(data);
      }
    } catch (error) {
      console.error("Failed to fetch company stats:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!companyStats) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-amber-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Company Not Found</h2>
          <p className="text-slate-600 mb-6">Please complete onboarding first.</p>
          <Link
            href="/onboarding"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors"
          >
            Go to Onboarding
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                <Building2 className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">{companyStats.name}</h1>
                <p className="text-sm text-slate-500">Network Intelligence Dashboard</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/onboarding"
                className="px-4 py-2 text-slate-600 hover:text-slate-900 font-medium transition-colors"
              >
                Back to Onboarding
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Network Size */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <span className="text-2xl font-bold text-slate-900">
                {companyStats.people_count.toLocaleString()}
              </span>
            </div>
            <h3 className="text-sm font-medium text-slate-600 mb-1">Network Size</h3>
            <p className="text-xs text-slate-500">LinkedIn connections imported</p>
          </motion.div>

          {/* Active Roles */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
                <Briefcase className="w-6 h-6 text-purple-600" />
              </div>
              <span className="text-2xl font-bold text-slate-900">
                {companyStats.roles_count}
              </span>
            </div>
            <h3 className="text-sm font-medium text-slate-600 mb-1">Active Roles</h3>
            <p className="text-xs text-slate-500">Hiring positions</p>
          </motion.div>

          {/* Import Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center">
                <Database className="w-6 h-6 text-green-600" />
              </div>
              {companyStats.linkedin_imported ? (
                <CheckCircle2 className="w-6 h-6 text-green-500" />
              ) : (
                <Clock className="w-6 h-6 text-amber-500" />
              )}
            </div>
            <h3 className="text-sm font-medium text-slate-600 mb-1">Data Import</h3>
            <p className="text-xs text-slate-500">
              {companyStats.linkedin_imported ? "LinkedIn imported" : "Pending import"}
            </p>
          </motion.div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Search Network */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Link
              href={`/agencity/search?company=${companyId}`}
              className="block group bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl p-8 text-white shadow-lg hover:shadow-xl transition-all"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-14 h-14 rounded-lg bg-white/20 flex items-center justify-center">
                  <Search className="w-7 h-7" />
                </div>
                <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
              </div>
              <h3 className="text-xl font-bold mb-2">Search Your Network</h3>
              <p className="text-blue-100 text-sm">
                Find candidates among your {companyStats.people_count.toLocaleString()} connections
              </p>
            </Link>
          </motion.div>

          {/* Timing Intelligence */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Link
              href={`/agencity/intelligence?company=${companyId}`}
              className="block group bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl p-8 text-white shadow-lg hover:shadow-xl transition-all"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-14 h-14 rounded-lg bg-white/20 flex items-center justify-center">
                  <TrendingUp className="w-7 h-7" />
                </div>
                <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
              </div>
              <h3 className="text-xl font-bold mb-2">Timing Intelligence</h3>
              <p className="text-purple-100 text-sm">
                See who's ready to make a move right now
              </p>
            </Link>
          </motion.div>
        </div>

        {/* Demo Info */}
        {companyId && DEMO_DATA[companyId as keyof typeof DEMO_DATA] && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-amber-50 border border-amber-200 rounded-xl p-6"
          >
            <div className="flex items-start gap-3">
              <Zap className="w-5 h-5 text-amber-600 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-amber-900 mb-2">
                  Demo Mode Active
                </h3>
                <p className="text-sm text-amber-800 mb-3">
                  You're viewing a pre-configured demo company with real data. This showcases how Agencity works with your LinkedIn network.
                </p>

                {companyId === "100b5ac1-1912-4970-a378-04d0169fd597" && (
                  <div className="bg-white/50 rounded-lg p-4 space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Linkedin className="w-4 h-4 text-blue-600" />
                      <span className="font-medium text-slate-700">3,637 connections imported</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <BarChart3 className="w-4 h-4 text-purple-600" />
                      <span className="font-medium text-slate-700">4 active roles ready to search</span>
                    </div>
                  </div>
                )}

                {companyId === "greptile-demo" && (
                  <div className="bg-white/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-sm">
                      <Briefcase className="w-4 h-4 text-blue-600" />
                      <span className="font-medium text-slate-700">YC W24 • AI Code Review • San Francisco</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm mt-8"
        >
          <h2 className="text-lg font-bold text-slate-900 mb-4">Getting Started</h2>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-50">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-900">Company profile created</p>
                <p className="text-xs text-slate-500">✓ {companyStats.name} is set up</p>
              </div>
            </div>

            <div className={`flex items-center gap-3 p-3 rounded-lg ${
              companyStats.linkedin_imported ? "bg-green-50" : "bg-slate-50"
            }`}>
              {companyStats.linkedin_imported ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : (
                <Clock className="w-5 h-5 text-slate-400" />
              )}
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-900">Import LinkedIn connections</p>
                <p className="text-xs text-slate-500">
                  {companyStats.linkedin_imported
                    ? `✓ ${companyStats.people_count.toLocaleString()} connections imported`
                    : "Upload your Connections.csv"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-lg bg-blue-50">
              <Search className="w-5 h-5 text-blue-500" />
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-900">Start searching</p>
                <p className="text-xs text-slate-500">Find candidates in your network</p>
              </div>
              <Link
                href={`/agencity/search?company=${companyId}`}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-colors"
              >
                Search Now
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
