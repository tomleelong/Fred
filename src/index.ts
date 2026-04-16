import { FredMCP } from "./mcp";

export { FredMCP };

export default {
	fetch(request: Request, env: Env, ctx: ExecutionContext) {
		const url = new URL(request.url);

		if (url.pathname === "/mcp") {
			return FredMCP.serve("/mcp").fetch(request, env, ctx);
		}

		if (url.pathname === "/sse" || url.pathname === "/sse/message") {
			return FredMCP.serveSSE("/sse").fetch(request, env, ctx);
		}

		if (url.pathname === "/") {
			return new Response(
				"FRED MCP Server — Federal Reserve Economic Data\n\n" +
					"Endpoints:\n" +
					"  /mcp   — Streamable HTTP MCP transport\n" +
					"  /sse   — Legacy SSE MCP transport\n",
				{ headers: { "content-type": "text/plain; charset=utf-8" } },
			);
		}

		return new Response("Not found", { status: 404 });
	},
} satisfies ExportedHandler<Env>;
