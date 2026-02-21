/**
 * curate_candidates — OpenClaw tool for AI-powered candidate curation.
 *
 * Takes a role description and candidate list, returns scored/ranked shortlist
 * with reasons for each candidate.
 */

import { Type } from "@sinclair/typebox";
import { agencityFetch, type ApiOpts } from "./api-client.js";

export function createCurationTool(opts: ApiOpts) {
  return {
    name: "curate_candidates",
    label: "Curate Candidates",
    description: [
      "Score and rank a list of candidates against a role description.",
      "Returns each candidate with a fit score, highlights, and concerns.",
      "Use this after candidate_search to narrow down a shortlist, or when the user",
      "asks to evaluate, rank, or compare candidates.",
    ].join(" "),

    parameters: Type.Object({
      role_title: Type.String({
        description: "The role these candidates are being evaluated for",
      }),
      required_skills: Type.Optional(
        Type.Array(Type.String(), {
          description: "Must-have skills for scoring",
        }),
      ),
      candidate_ids: Type.Optional(
        Type.Array(Type.String(), {
          description: "Specific candidate UUIDs to curate. If omitted, curates recent search results.",
        }),
      ),
      company_id: Type.Optional(
        Type.String({
          description: "Company UUID",
        }),
      ),
      limit: Type.Optional(
        Type.Number({
          description: "Max candidates to return (default: 10)",
        }),
      ),
    }),

    async execute(_id: string, params: Record<string, unknown>) {
      const roleTitle = typeof params.role_title === "string" ? params.role_title : "";
      if (!roleTitle.trim()) {
        throw new Error("role_title is required");
      }

      const body: Record<string, unknown> = {
        role_title: roleTitle,
        required_skills: Array.isArray(params.required_skills) ? params.required_skills : [],
        limit: typeof params.limit === "number" ? params.limit : 10,
      };

      if (Array.isArray(params.candidate_ids)) {
        body.candidate_ids = params.candidate_ids;
      }
      if (typeof params.company_id === "string" && params.company_id.trim()) {
        body.company_id = params.company_id;
      }

      const result = await agencityFetch(opts, "/api/curate", body);

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
