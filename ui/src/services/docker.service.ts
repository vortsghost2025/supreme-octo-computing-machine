/**
 * Docker / SNAC backend service helpers.
 * Fetches real data from the orchestration layer running at
 *   http://snac_backend:8000/orchestration/agents
 *
 * The function returns the parsed JSON payload (an array of agents).
 * It throws an Error if the HTTP request fails or the response is not JSON.
 */
export async function fetchAgents(): Promise<any[]> {
  const url = 'http://snac_backend:8000/orchestration/agents';
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch agents – ${response.status} ${response.statusText}`);
  }
  const data = await response.json();
  // Expect the backend to return an array; guard against unexpected shapes.
  if (!Array.isArray(data)) {
    throw new Error('Agents endpoint returned non‑array payload');
  }
  return data;
}
