/**
 * network_intel — OpenClaw tool for network/relationship intelligence.
 *
 * Surfaces warm paths, mutual connections, and relationship context
 * between the hiring company's network and potential candidates.
 */

import { Type } from "@sinclair/typebox";
import { agencityFetch, type ApiOpts } from "./api-client.js";

export function createNetworkIntelTool(opts: ApiOpts) {
  return {
    name: "network_intel",
    label: "Network Intelligence",
    description: [
      "Find warm paths and relationship context for reaching a candidate.",
      "Shows mutual connections, shared employers, and the best introduction strategy.",
      "Use this when the user asks 'how do I reach this person?', 'who can introduce me?',",
      "or wants to understand the relationship between their network and a candidate.",
    ].join(" "),

    parameters: Type.Object({
      company_id: Type.String({ description: "Company UUID (required)" }),
      candidate_name: Type.Optional(
        Type.String({
          description: "Full name of the candidate to research",
        }),
      ),
      candidate_id: Type.Optional(
        Type.String({
          description: "Candidate UUID from a previous search",
        }),
      ),
      linkedin_url: Type.Optional(
        Type.String({
          description: "LinkedIn profile URL of the candidate",
        }),
      ),
    }),

    async execute(_id: string, params: Record<string, unknown>) {
      const companyId = typeof params.company_id === "string" ? params.company_id.trim() : "";
      if (!companyId) {
        throw new Error("company_id is required for network intelligence lookups");
      }

      const candidateName =
        typeof params.candidate_name === "string" ? params.candidate_name : "";
      const candidateId =
        typeof params.candidate_id === "string" ? params.candidate_id : "";

      if (!candidateName.trim() && !candidateId.trim()) {
        throw new Error(
          "Provide either candidate_name or candidate_id to look up network intelligence",
        );
      }

      const body: Record<string, unknown> = {};
      if (candidateName.trim()) body.candidate_name = candidateName;
      if (candidateId.trim()) body.candidate_id = candidateId;
      if (typeof params.linkedin_url === "string" && params.linkedin_url.trim()) {
        body.linkedin_url = params.linkedin_url;
      }

      // POST /api/v3/expansion/warm-paths/{company_id}
      const result = await agencityFetch(
        opts,
        `/api/v3/expansion/warm-paths/${companyId}`,
        body,
      );

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
