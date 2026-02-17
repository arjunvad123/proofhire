/**
 * Initialize localStorage for Confido demo
 * Run this in the browser console to set up the demo environment
 */

const confidoData = {
  companyId: "100b5ac1-1912-4970-a378-04d0169fd597",
  company: {
    id: "100b5ac1-1912-4970-a378-04d0169fd597",
    name: "Confido",
    domain: "confidotech.com",
    industry: "Fintech",
    tech_stack: ["Python", "React", "AI/ML", "PostgreSQL"],
    team_size: 28,
    founder_email: "arjun@confido.com",
    founder_name: "Arjun Vad",
    founder_linkedin_url: null,
    linkedin_imported: true,
    existing_db_imported: false,
    onboarding_complete: true,
    people_count: 3637,
    roles_count: 5,
  },
  umo: {
    id: "b51534f6-4cda-4223-b332-3530cc44e2e8",
    company_id: "100b5ac1-1912-4970-a378-04d0169fd597",
    preferred_backgrounds: ["Startup experience", "Fast-paced environment"],
    must_have_traits: ["Self-starter", "Strong communicator"],
    anti_patterns: ["Needs heavy direction", "Slow to ship"],
    culture_values: ["Move fast", "Customer obsessed", "Data-driven"],
    work_style: "Remote-first",
    ideal_candidate_description: "Thrives in ambiguity",
  },
  roles: [
    {
      id: "25a77e56-70a6-412a-9364-04aab23461fa",
      title: "Software Engineer",
      level: "senior",
      department: "Engineering",
      required_skills: ["Python", "React"],
      status: "active",
    },
    {
      id: "1838aaf4-6713-419a-ac6f-86e553a4f5b4",
      title: "Founding Growth",
      department: "Growth",
      required_skills: ["Growth Marketing", "B2B", "Analytics"],
      status: "active",
    },
    {
      id: "8bdd4d31-10b9-4f3c-8dbc-bb92f16a3b8b",
      title: "Head of Finance",
      department: "Finance",
      required_skills: ["FP&A", "CPG", "Financial Modeling"],
      status: "active",
    },
  ],
  linkedinImport: {
    id: "cbe7ea03-0496-4163-81be-8f416e97124d",
    type: "linkedin_export",
    name: "Connections.csv",
    total_records: 3637,
    records_created: 3636,
    status: "completed",
  },
  databaseImport: null,
  currentStep: 6,
  isComplete: true,
};

// Set localStorage
localStorage.setItem("onboarding-state", JSON.stringify(confidoData));

console.log("✅ Demo environment initialized for Confido!");
console.log("Company ID:", confidoData.companyId);
console.log("Network Size:", confidoData.company.people_count);
console.log("Active Roles:", confidoData.company.roles_count);
console.log("\nRefresh the page to see the changes.");
