import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { McpAgent } from "agents/mcp";
import { z } from "zod";

import { FredAPIError, FredClient } from "./fred-client";

function errorText(err: unknown): string {
	if (err instanceof FredAPIError) return err.message;
	if (err instanceof Error) return err.message;
	return String(err);
}

function textResult(text: string) {
	return { content: [{ type: "text" as const, text }] };
}

export class FredMCP extends McpAgent<Env> {
	server = new McpServer({
		name: "FRED MCP",
		version: "0.1.0",
	});

	private getClient(): FredClient {
		const key = this.env.FRED_API_KEY;
		if (!key) {
			throw new Error(
				"FRED_API_KEY is not set. Run: wrangler secret put FRED_API_KEY",
			);
		}
		return new FredClient(key);
	}

	async init() {
		this.server.registerTool(
			"search_series",
			{
				description:
					"Search FRED for economic data series by keyword. " +
					"Returns matching series with IDs, titles, frequency, units, and date ranges.",
				inputSchema: {
					query: z
						.string()
						.describe(
							'Search terms (e.g. "GDP", "unemployment rate", "consumer price index").',
						),
					limit: z
						.number()
						.int()
						.default(10)
						.describe("Max number of results to return (default 10, max 1000)."),
				},
			},
			async ({ query, limit }) => {
				try {
					const data = await this.getClient().searchSeries(query, limit);
					const seriesList = data.seriess ?? [];
					if (seriesList.length === 0) {
						return textResult(`No series found for '${query}'.`);
					}
					const lines = [
						`Found ${data.count ?? seriesList.length} series (showing ${seriesList.length}):\n`,
					];
					for (const s of seriesList) {
						lines.push(
							`- **${s.id}**: ${s.title}\n` +
								`  Frequency: ${s.frequency ?? "N/A"} | ` +
								`Units: ${s.units ?? "N/A"} | ` +
								`Seasonal: ${s.seasonal_adjustment ?? "N/A"}\n` +
								`  Range: ${s.observation_start ?? "?"} to ${s.observation_end ?? "?"}`,
						);
					}
					return textResult(lines.join("\n"));
				} catch (err) {
					return textResult(errorText(err));
				}
			},
		);

		this.server.registerTool(
			"get_series",
			{
				description:
					"Get metadata for a specific FRED series (title, units, frequency, date range).",
				inputSchema: {
					series_id: z
						.string()
						.describe('FRED series ID (e.g. "GDP", "UNRATE", "CPIAUCSL", "DFF", "SP500").'),
				},
			},
			async ({ series_id }) => {
				try {
					const data = await this.getClient().getSeries(series_id);
					const seriesList = data.seriess ?? [];
					if (seriesList.length === 0) {
						return textResult(`Series '${series_id}' not found.`);
					}
					const s = seriesList[0];
					const notes = (s.notes ?? "N/A").slice(0, 500);
					return textResult(
						`**${s.id}**: ${s.title}\n\n` +
							`- Frequency: ${s.frequency ?? "N/A"}\n` +
							`- Units: ${s.units ?? "N/A"}\n` +
							`- Seasonal adjustment: ${s.seasonal_adjustment ?? "N/A"}\n` +
							`- Observation range: ${s.observation_start ?? "?"} to ${s.observation_end ?? "?"}\n` +
							`- Last updated: ${s.last_updated ?? "N/A"}\n` +
							`- Notes: ${notes}`,
					);
				} catch (err) {
					return textResult(errorText(err));
				}
			},
		);

		this.server.registerTool(
			"get_observations",
			{
				description:
					"Get time series observations (data points) for a FRED series. " +
					"Returns a formatted markdown table of date/value pairs.",
				inputSchema: {
					series_id: z.string().describe('FRED series ID (e.g. "GDP", "UNRATE").'),
					start_date: z
						.string()
						.optional()
						.describe("Start date in YYYY-MM-DD format."),
					end_date: z
						.string()
						.optional()
						.describe("End date in YYYY-MM-DD format."),
					frequency: z
						.string()
						.optional()
						.describe("Aggregation frequency — d, w, bw, m, q, sa, a."),
					units: z
						.string()
						.optional()
						.describe(
							"Data transformation — lin (default), chg, ch1, pch, pc1, pca, cch, cca, log.",
						),
					limit: z
						.number()
						.int()
						.default(100)
						.describe("Max observations (default 100, max 100000)."),
					sort_order: z
						.enum(["asc", "desc"])
						.default("desc")
						.describe('"asc" (oldest first) or "desc" (newest first, default).'),
				},
			},
			async ({ series_id, start_date, end_date, frequency, units, limit, sort_order }) => {
				try {
					const data = await this.getClient().getObservations(series_id, {
						observation_start: start_date,
						observation_end: end_date,
						frequency,
						units,
						limit,
						sort_order,
					});
					const observations = data.observations ?? [];
					if (observations.length === 0) {
						return textResult(`No observations found for '${series_id}'.`);
					}
					const count = data.count ?? observations.length;
					const lines = [
						`**${series_id}** — ${count} total observations (showing ${observations.length}):\n`,
						"| Date | Value |",
						"|------|-------|",
					];
					for (const obs of observations) {
						lines.push(`| ${obs.date} | ${obs.value} |`);
					}
					return textResult(lines.join("\n"));
				} catch (err) {
					return textResult(errorText(err));
				}
			},
		);

		this.server.registerTool(
			"get_category",
			{
				description:
					"Get information about a FRED category. Root category (id=0) contains all top-level categories.",
				inputSchema: {
					category_id: z
						.number()
						.int()
						.default(0)
						.describe("FRED category ID (default 0 for root)."),
				},
			},
			async ({ category_id }) => {
				try {
					const data = await this.getClient().getCategory(category_id);
					const categories = data.categories ?? [];
					if (categories.length === 0) {
						return textResult(`Category ${category_id} not found.`);
					}
					const c = categories[0];
					return textResult(
						`**Category ${c.id}**: ${c.name}\n` +
							`- Parent ID: ${c.parent_id ?? "N/A"}`,
					);
				} catch (err) {
					return textResult(errorText(err));
				}
			},
		);

		this.server.registerTool(
			"get_category_children",
			{
				description:
					"List child categories within a FRED category. " +
					"Start with category_id=0 for all top-level categories, then drill down.",
				inputSchema: {
					category_id: z
						.number()
						.int()
						.default(0)
						.describe("Parent category ID (default 0 for root)."),
				},
			},
			async ({ category_id }) => {
				try {
					const data = await this.getClient().getCategoryChildren(category_id);
					const categories = data.categories ?? [];
					if (categories.length === 0) {
						return textResult(
							`No child categories found for category ${category_id}.`,
						);
					}
					const lines = [`Children of category ${category_id}:\n`];
					for (const c of categories) {
						lines.push(`- **${c.id}**: ${c.name}`);
					}
					return textResult(lines.join("\n"));
				} catch (err) {
					return textResult(errorText(err));
				}
			},
		);
	}
}
