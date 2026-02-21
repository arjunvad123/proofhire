/**
 * Agencity OpenClaw Plugin
 *
 * Registers hiring tools with the OpenClaw agent:
 *   - candidate_search: Find candidates via the unified search API
 *   - curate_candidates: Score and rank a shortlist
 *   - pipeline_status: Check hiring pipeline for a company
 *   - network_intel: Relationship/warm-path intelligence
 *
 * The plugin calls the Agencity FastAPI backend over HTTP.
 */

// NOTE: openclaw/plugin-sdk is resolved at runtime via jiti alias.
// For type checking in dev, use openclaw as a devDependency or reference the types directly.
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { createSearchTool } from "./src/search-tool.js";
import { createCurationTool } from "./src/curation-tool.js";
import { createPipelineTool } from "./src/pipeline-tool.js";
import { createNetworkIntelTool } from "./src/network-intel-tool.js";

type AgencityConfig = {
  apiBase?: string;
  apiKey?: string;
  defaultMode?: string;
  timeoutMs?: number;
};

const plugin = {
  id: "agencity",
  name: "Agencity",
  description: "AI hiring agent — candidate search, curation, and pipeline management",

  register(api: OpenClawPluginApi) {
    const config: AgencityConfig = (api.pluginConfig ?? {}) as AgencityConfig;
    const baseUrl = config.apiBase ?? "http://localhost:8001";
    const apiKey = config.apiKey ?? "";
    const timeoutMs = config.timeoutMs ?? 60_000;

    api.logger.info(`Agencity plugin loaded — API: ${baseUrl}`);

    // Register all hiring tools
    api.registerTool(createSearchTool({ baseUrl, apiKey, timeoutMs, config }));
    api.registerTool(createCurationTool({ baseUrl, apiKey, timeoutMs }));
    api.registerTool(createPipelineTool({ baseUrl, apiKey, timeoutMs }));
    api.registerTool(createNetworkIntelTool({ baseUrl, apiKey, timeoutMs }));
  },
};

export default plugin;
