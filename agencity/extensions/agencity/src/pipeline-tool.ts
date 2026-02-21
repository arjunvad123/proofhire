/**
 * pipeline_status — OpenClaw tool for viewing and managing the hiring pipeline.
 *
 * Shows candidates in various stages (sourced, screening, interview, offer, etc.)
 * and allows moving candidates through the pipeline.
 */

import { Type } from "@sinclair/typebox";
import { agencityFetch, agencityGet, type ApiOpts } from "./api-client.js";

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
      company_id: Type.Optional(
        Type.String({ description: "Company UUID" }),
      ),
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
      const action =
        typeof params.action === "string" ? params.action : "view";

      if (action === "update") {
        // Update a candidate's pipeline status
        const candidateId = typeof params.candidate_id === "string" ? params.candidate_id : "";
        const newStatus = typeof params.new_status === "string" ? params.new_status : "";

        if (!candidateId.trim()) {
          throw new Error("candidate_id is required for pipeline updates");
        }
        if (!newStatus.trim()) {
          throw new Error("new_status is required (e.g. 'screening', 'interview', 'offer')");
        }

        const body: Record<string, unknown> = {
          candidate_id: candidateId,
          new_status: newStatus,
        };
        if (typeof params.feedback === "string") {
          body.feedback = params.feedback;
        }
        if (typeof params.company_id === "string") {
          body.company_id = params.company_id;
        }

        const result = await agencityFetch(
          opts,
          `/api/integration/pipeline/${candidateId}/status`,
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

      // Default: view pipeline
      let path = "/api/integration/pipeline";
      const queryParams: string[] = [];
      if (typeof params.company_id === "string" && params.company_id.trim()) {
        queryParams.push(`company_id=${encodeURIComponent(params.company_id)}`);
      }
      if (typeof params.role_id === "string" && params.role_id.trim()) {
        queryParams.push(`role_id=${encodeURIComponent(params.role_id)}`);
      }
      if (queryParams.length > 0) {
        path += `?${queryParams.join("&")}`;
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
