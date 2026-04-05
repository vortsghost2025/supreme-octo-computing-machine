import { useEffect, useState } from 'react';
import { fetchAgents } from '../services/docker.service';

/**
 * Simple panel that displays the list of agents fetched from the real backend.
 * Shows id, role, and current status. If the fetch fails, an error message
 * is rendered so the UI does not crash.
 */
export default function AgentsPanel() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const data = await fetchAgents();
        if (!cancelled) {
          setAgents(data);
          setLoading(false);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e.message || 'Failed to load agents');
          setLoading(false);
        }
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="panel">
        <div className="panel-header"><h2>🤖 Agents</h2></div>
        <div className="panel-content"><div className="loading">Loading agents...</div></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel">
        <div className="panel-header"><h2>🤖 Agents</h2></div>
        <div className="panel-content"><div className="error" style={{ color: '#f85149' }}>{error}</div></div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🤖 Agents</h2>
        <span className="badge">{agents.length}</span>
      </div>
      <div className="panel-content">
        {agents.length === 0 ? (
          <div className="empty">No agents reported.</div>
        ) : (
          <table className="agents-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>ID</th>
                <th style={{ textAlign: 'left' }}>Role</th>
                <th style={{ textAlign: 'left' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((a) => (
                <tr key={a.id}>
                  <td>{a.id}</td>
                  <td>{a.role || a.type || '—'}</td>
                  <td>{a.status || 'unknown'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
