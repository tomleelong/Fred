const DEFAULT_BASE_URL = "https://api.stlouisfed.org/fred";

export class FredAPIError extends Error {
	constructor(
		public readonly status: number,
		message: string,
	) {
		super(`FRED API error (${status}): ${message}`);
		this.name = "FredAPIError";
	}
}

export interface FredSeries {
	id: string;
	title: string;
	frequency?: string;
	units?: string;
	seasonal_adjustment?: string;
	observation_start?: string;
	observation_end?: string;
	last_updated?: string;
	notes?: string;
}

export interface FredCategory {
	id: number;
	name: string;
	parent_id?: number;
}

export interface FredObservation {
	date: string;
	value: string;
}

export class FredClient {
	private readonly baseUrl: string;

	constructor(
		private readonly apiKey: string,
		baseUrl: string = DEFAULT_BASE_URL,
	) {
		this.baseUrl = baseUrl;
	}

	private async get<T>(path: string, params: Record<string, string | number> = {}): Promise<T> {
		const url = new URL(`${this.baseUrl}${path}`);
		url.searchParams.set("api_key", this.apiKey);
		url.searchParams.set("file_type", "json");
		for (const [k, v] of Object.entries(params)) {
			url.searchParams.set(k, String(v));
		}

		const response = await fetch(url.toString());
		if (!response.ok) {
			const body = (await response.text()).slice(0, 500);
			if (response.status === 429) {
				throw new FredAPIError(
					429,
					`${body} — rate limit (120 req/min) exceeded.`,
				);
			}
			throw new FredAPIError(response.status, body);
		}
		return (await response.json()) as T;
	}

	searchSeries(searchText: string, limit = 10) {
		return this.get<{ count?: number; seriess: FredSeries[] }>("/series/search", {
			search_text: searchText,
			limit,
		});
	}

	getSeries(seriesId: string) {
		return this.get<{ seriess: FredSeries[] }>("/series", { series_id: seriesId });
	}

	getObservations(
		seriesId: string,
		opts: {
			observation_start?: string;
			observation_end?: string;
			frequency?: string;
			units?: string;
			limit?: number;
			sort_order?: string;
		} = {},
	) {
		const params: Record<string, string | number> = { series_id: seriesId };
		if (opts.observation_start) params.observation_start = opts.observation_start;
		if (opts.observation_end) params.observation_end = opts.observation_end;
		if (opts.frequency) params.frequency = opts.frequency;
		if (opts.units) params.units = opts.units;
		if (opts.limit !== undefined) params.limit = opts.limit;
		if (opts.sort_order) params.sort_order = opts.sort_order;
		return this.get<{ count?: number; observations: FredObservation[] }>(
			"/series/observations",
			params,
		);
	}

	getCategory(categoryId = 0) {
		return this.get<{ categories: FredCategory[] }>("/category", { category_id: categoryId });
	}

	getCategoryChildren(categoryId = 0) {
		return this.get<{ categories: FredCategory[] }>("/category/children", {
			category_id: categoryId,
		});
	}
}
