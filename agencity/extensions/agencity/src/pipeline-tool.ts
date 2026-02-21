/**
 * pipeline_status — OpenClaw tool for viewing and managing the hiring pipeline.
 *
 * Shows candidates in various stages (sourced, screening, interview, offer, etc.)
 * and allows moving candidates through the pipeline.
 */

import { Type } from "@sinclair/typebox";
import { agencityGet, agencityPatch, type ApiOpts } from "./api-client.js";

export function createPipelineTool(opts: ApiOpts) {
  return {
    name: "pipeline_status",
    label: "Pipeline Status",
    description: [
      "View the current hiring pipeline for a company or role.",
      "Shows candidates organized by stage: sourced, screening, interview, offer, hired.",
      "Can also update a candidate's status in the pipeline.",
      "Use this when the user asks about their pipeline, hiring progress, or candidate status.",
    ].join(" "),

    parameters: Type.Object({
      action: Type.Optional(
        Type.String({
          description:
            "'view' to see the pipeline (default), 'update' to move a candidate to a new stage",
        }),
      ),
      company_id: Type.String({ description: "Company UUID (required)" }),
      role_id: Type.Optional(
        Type.String({ description: "Filter by role/search UUID" }),
      ),
      candidate_id: Type.Optional(
        Type.String({
          description: "Candidate UUID (required for 'update' action)",
        }),
      ),
      new_status: Type.Optional(
        Type.String({
          description:
            "New pipeline status: 'sourced', 'screening', 'interview', 'offer', 'hired', 'rejected'",
        }),
      ),
      feedback: Type.Optional(
        Type.String({
          description: "Notes or feedback when updating status",
        }),
      ),
    }),

    async execute(_id: string, params: Record<string, unknown>) {
      const action = typeof params.action === "string" ? params.action : "view";
      const companyId = typeof params.company_id === "string" ? params.company_id.trim() : "";

      if (!companyId) {
        throw new Error("company_id is required");
      }

      if (action === "update") {
        // PATCH /api/candidates/{id}/status
        const candidateId = typeof params.candidate_id === "string" ? params.candidate_id : "";
        const newStatus = typeof params.new_status === "string" ? params.new_status : "";

        if (!candidateId.trim()) {
          throw new Error("candidate_id is required for pipeline updates");
        }
        if (!newStatus.trim()) {
          throw new Error("new_status is required (e.g. 'screening', 'interview', 'offer')");
        }

        const body: Record<string, unknown> = { status: newStatus };
        if (typeof params.feedback === "string") {
          body.feedback = params.feedback;
        }

        const result = await agencityPatch(
          opts,
          `/api/candidates/${candidateId}/status`,
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
      }

      // Default: GET /api/pipeline/{company_id}
      let path = `/api/pipeline/${companyId}`;
      if (typeof params.role_id === "string" && params.role_id.trim()) {
        path += `?role_id=${encodeURIComponent(params.role_id)}`;
      }

      const result = await agencityGet(opts, path);

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
