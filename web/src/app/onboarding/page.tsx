"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Building2,
  Rocket,
  Upload,
  UserPlus,
  CheckCircle2,
  ArrowRight,
  Zap
} from "lucide-react";

// Pre-configured company profiles
const DEMO_COMPANIES = {
  greptile: {
    id: "greptile-demo",
    name: "Greptile",
    description: "AI code review agent (YC W24)",
    role: "Software Engineer (Generalist)",
    color: "from-blue-500 to-cyan-500",
    logo: "🔍",
  },
  confido: {
    id: "100b5ac1-1912-4970-a378-04d0169fd597",
    name: "Confido",
    description: "Healthcare startup with 3,637 LinkedIn connections",
    role: "Software Engineer",
    color: "from-purple-500 to-pink-500",
    logo: "🏥",
  },
};

interface Step {
  number: number;
  title: string;
  description: string;
  icon: React.ReactNode;
  status: "pending" | "current" | "completed";
}

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [companyData, setCompanyData] = useState({
    name: "",
    domain: "",
    founderEmail: "",
    founderName: "",
  });

  const steps: Step[] = [
    {
      number: 1,
      title: "Company Info",
      description: "Tell us about your company",
      icon: <Building2 className="w-5 h-5" />,
      status: currentStep === 1 ? "current" : currentStep > 1 ? "completed" : "pending",
    },
    {
      number: 2,
      title: "Import Network",
      description: "Upload LinkedIn connections",
      icon: <Upload className="w-5 h-5" />,
      status: currentStep === 2 ? "current" : currentStep > 2 ? "completed" : "pending",
    },
    {
      number: 3,
      title: "Create Role",
      description: "Add your first hiring position",
      icon: <UserPlus className="w-5 h-5" />,
      status: currentStep === 3 ? "current" : currentStep > 3 ? "completed" : "pending",
    },
    {
      number: 4,
      title: "Start Searching",
      description: "Find candidates in your network",
      icon: <Rocket className="w-5 h-5" />,
      status: currentStep === 4 ? "current" : "pending",
    },
  ];

  const handleDemoCompany = (companyKey: "greptile" | "confido") => {
    const company = DEMO_COMPANIES[companyKey];

    // Store company ID in localStorage
    localStorage.setItem("onboarding-state", JSON.stringify({
      companyId: company.id,
      company: {
        name: company.name,
        id: company.id,
      },
      step: "complete",
    }));

    // Redirect to dashboard
    router.push(`/agencity/dashboard?company=${company.id}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Quick Access Header */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                <Rocket className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Agencity Setup</h1>
                <p className="text-sm text-slate-500">Get started in minutes</p>
              </div>
            </div>

            {/* Quick Access Buttons */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 mr-4">
                <Zap className="w-4 h-4 text-amber-500" />
                <span className="text-sm font-medium text-slate-600">Quick Access:</span>
              </div>

              {/* Greptile Button */}
              <button
                onClick={() => handleDemoCompany("greptile")}
                className="group relative px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-200 flex items-center gap-2"
              >
                <span className="text-xl">{DEMO_COMPANIES.greptile.logo}</span>
                <div className="text-left">
                  <div className="text-sm font-semibold">Greptile</div>
                  <div className="text-xs opacity-90">YC W24</div>
                </div>
                <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-0.5 transition-transform" />
              </button>

              {/* Confido Button */}
              <button
                onClick={() => handleDemoCompany("confido")}
                className="group relative px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-200 flex items-center gap-2"
              >
                <span className="text-xl">{DEMO_COMPANIES.confido.logo}</span>
                <div className="text-left">
                  <div className="text-sm font-semibold">Confido</div>
                  <div className="text-xs opacity-90">3,637 connections</div>
                </div>
                <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Progress Steps */}
        <div className="mb-12">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center flex-1">
                {/* Step Circle */}
                <div className="relative">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 ${
                      step.status === "completed"
                        ? "bg-green-500 text-white"
                        : step.status === "current"
                        ? "bg-blue-500 text-white ring-4 ring-blue-100"
                        : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    {step.status === "completed" ? (
                      <CheckCircle2 className="w-6 h-6" />
                    ) : (
                      step.icon
                    )}
                  </div>
                  <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 text-center whitespace-nowrap">
                    <div className={`text-sm font-medium ${
                      step.status === "current" ? "text-blue-600" : "text-slate-600"
                    }`}>
                      {step.title}
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {step.description}
                    </div>
                  </div>
                </div>

                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div className="flex-1 h-1 mx-4">
                    <div
                      className={`h-full transition-all duration-300 ${
                        step.status === "completed"
                          ? "bg-green-500"
                          : "bg-slate-200"
                      }`}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="mt-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl shadow-xl p-8 border border-slate-200"
          >
            {currentStep === 1 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900 mb-2">
                    Tell us about your company
                  </h2>
                  <p className="text-slate-600">
                    We'll use this to personalize your candidate search
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Company Name *
                    </label>
                    <input
                      type="text"
                      value={companyData.name}
                      onChange={(e) =>
                        setCompanyData({ ...companyData, name: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Acme Inc"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Domain
                    </label>
                    <input
                      type="text"
                      value={companyData.domain}
                      onChange={(e) =>
                        setCompanyData({ ...companyData, domain: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="acme.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Founder Name *
                    </label>
                    <input
                      type="text"
                      value={companyData.founderName}
                      onChange={(e) =>
                        setCompanyData({ ...companyData, founderName: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Jane Doe"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Founder Email *
                    </label>
                    <input
                      type="email"
                      value={companyData.founderEmail}
                      onChange={(e) =>
                        setCompanyData({ ...companyData, founderEmail: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="jane@acme.com"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <button
                    onClick={() => setCurrentStep(2)}
                    disabled={!companyData.name || !companyData.founderEmail || !companyData.founderName}
                    className="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-300 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
                  >
                    Continue
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {currentStep === 2 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900 mb-2">
                    Import your LinkedIn network
                  </h2>
                  <p className="text-slate-600">
                    Upload your Connections.csv from LinkedIn to build your candidate pool
                  </p>
                </div>

                <div className="border-2 border-dashed border-slate-300 rounded-xl p-12 text-center hover:border-blue-400 transition-colors">
                  <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                  <p className="text-slate-700 font-medium mb-2">
                    Drop your LinkedIn Connections.csv here
                  </p>
                  <p className="text-sm text-slate-500 mb-4">
                    or click to browse
                  </p>
                  <input
                    type="file"
                    accept=".csv"
                    className="hidden"
                    id="csv-upload"
                  />
                  <label
                    htmlFor="csv-upload"
                    className="inline-block px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg cursor-pointer transition-colors"
                  >
                    Choose File
                  </label>
                </div>

                <div className="flex justify-between pt-4">
                  <button
                    onClick={() => setCurrentStep(1)}
                    className="px-6 py-3 border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium rounded-lg transition-colors"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => setCurrentStep(3)}
                    className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
                  >
                    Continue
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        </div>

        {/* Demo Info Card */}
        <div className="mt-8 p-6 bg-amber-50 border border-amber-200 rounded-xl">
          <div className="flex items-start gap-3">
            <Zap className="w-5 h-5 text-amber-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-900 mb-1">
                Want to see it in action?
              </h3>
              <p className="text-sm text-amber-800 mb-3">
                Click the <strong>Greptile</strong> or <strong>Confido</strong> buttons above to jump directly into a pre-configured demo with real data.
              </p>
              <div className="flex gap-4 text-xs text-amber-700">
                <div>
                  <strong>Greptile:</strong> YC W24 company profile
                </div>
                <div>
                  <strong>Confido:</strong> 3,637 LinkedIn connections imported
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
