
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface GraphStats {
    node_count: number;
    edge_count: number;
    density: number;
}

export interface CausalResults {
    coefficients: {
        intercept: number;
        degree_centrality: number;
        is_manager: number;
    };
    r_squared: number;
}

export interface TaskResponse {
    task_id: string;
    status: string;
    result?: CausalResults;
}

// ETag cache for conditional requests
const etagCache = new Map<string, string>();

export const api = {
    getStats: async (): Promise<GraphStats> => {
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
        };

        // Add If-None-Match header if we have a cached ETag
        const cachedEtag = etagCache.get('graph_stats');
        if (cachedEtag) {
            headers['If-None-Match'] = cachedEtag;
        }

        const res = await fetch(`${API_URL}/api/graph/stats`, { headers });

        // Handle 304 Not Modified - use cached data
        if (res.status === 304) {
            const cached = localStorage.getItem('cached_graph_stats');
            if (cached) {
                return JSON.parse(cached);
            }
        }

        // Store new ETag
        const etag = res.headers.get('ETag');
        if (etag) {
            etagCache.set('graph_stats', etag);
            // Cache the response
            const data = await res.json();
            localStorage.setItem('cached_graph_stats', JSON.stringify(data));
            return data;
        }

        return res.json();
    },

    getStatsWithETag: async (): Promise<{ data: GraphStats; etag: string | null }> => {
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
        };

        const cachedEtag = etagCache.get('graph_stats');
        if (cachedEtag) {
            headers['If-None-Match'] = cachedEtag;
        }

        const res = await fetch(`${API_URL}/api/graph/stats`, { headers });

        if (res.status === 304) {
            const cached = localStorage.getItem('cached_graph_stats');
            return {
                data: cached ? JSON.parse(cached) : null,
                etag: cachedEtag
            };
        }

        const data = await res.json();
        const etag = res.headers.get('ETag');

        if (etag) {
            etagCache.set('graph_stats', etag);
            localStorage.setItem('cached_graph_stats', JSON.stringify(data));
        }

        return { data, etag };
    },

    // Phase 2: Async Analysis
    triggerAnalysis: async (): Promise<{ task_id: string }> => {
        const res = await fetch(`${API_URL}/api/causal/analyze`, { method: 'POST' });
        return res.json();
    },

    pollTask: async (taskId: string): Promise<TaskResponse> => {
        const res = await fetch(`${API_URL}/api/tasks/${taskId}`);
        return res.json();
    }
};
