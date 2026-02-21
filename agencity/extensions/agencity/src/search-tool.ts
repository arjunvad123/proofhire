/**
 * candidate_search — OpenClaw tool that calls the Agencity unified search API.
 *
 * When the user says something like "Find me a founding engineer with Python
 * and React in SF", the OpenClaw agent will call this tool.
 */

import { Type } from "@sinclair/typebox";
import { agencityFetch, type ApiOpts } from "./api-client.js";

type SearchToolOpts = ApiOpts & {
  config: { defaultMode?: string };
};

export function createSearchTool(opts: SearchToolOpts) {
  return {
    name: "candidate_search",
    label: "Candidate Search",
    description: [
      "Search for candidates matching a role description.",
      "Returns ranked candidates with fit scores, warm paths, and timing signals.",
      "Use this whenever the user asks to find, search, or source candidates.",
    ].join(" "),

    parameters: Type.Object({
      role_title: Type.String({
        description: "The job title or role to search for (e.g. 'Senior Backend Engineer')",
      }),
      required_skills: Type.Optional(
        Type.Array(Type.String(), {
          description: "Skills the candidate must have (e.g. ['Python', 'FastAPI', 'PostgreSQL'])",
        }),
      ),
      preferred_skills: Type.Optional(
        Type.Array(Type.String(), {
          description: "Nice-to-have skills (e.g. ['React', 'TypeScript'])",
        }),
      ),
      location: Type.Optional(
        Type.String({
          description: "Preferred location or 'remote' (e.g. 'San Francisco, CA')",
        }),
      ),
      years_experience: Type.Optional(
        Type.Number({
          description: "Minimum years of experience",
        }),
      ),
      company_id: Type.Optional(
        Type.String({
          description: "Company UUID (uses default if not provided)",
        }),
      ),
      mode: Type.Optional(
        Type.String({
          description: "Search depth: 'quick' (fast, network+external), 'full' (deep research), or 'network_only'",
        }),
      ),
    }),

    async execute(_id: string, params: Record<string, unknown>) {
      const roleTitle = typeof params.role_title === "string" ? params.role_title : "";
      if (!roleTitle.trim()) {
        throw new Error("role_title is required — what role are you hiring for?");
      }

      const mode =
        (typeof params.mode === "string" && params.mode.trim()) ||
        opts.config.defaultMode ||
        "quick";

      const body: Record<string, unknown> = {
        role_title: roleTitle,
        required_skills: Array.isArray(params.required_skills) ? params.required_skills : [],
        preferred_skills: Array.isArray(params.preferred_skills) ? params.preferred_skills : [],
        location: typeof params.location === "string" ? params.location : null,
        years_experience: typeof params.years_experience === "number" ? params.years_experience : null,
        include_external: mode !== "network_only",
        include_timing: mode !== "network_only",
        deep_research: mode === "full",
      };

      if (typeof params.company_id === "string" && params.company_id.trim()) {
        body.company_id = params.company_id;
      }

      const result = await agencityFetch(opts, "/api/search", body);

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    },
  };
}
