import React, { useState, useEffect } from 'react';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('insights');
  const [insights, setInsights] = useState([]);
  const [data, setData] = useState({ events: [], metrics: [] });
  const [sources, setSources] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/sources')
      .then(res => res.json())
      .then(d => setSources(d.sources || []))
      .catch(console.error);
      
    fetch('http://127.0.0.1:8000/api/insights')
      .then(res => res.json())
      .then(d => setInsights(d.insights || []))
      .catch(console.error);
      
    fetch('http://127.0.0.1:8000/api/data')
      .then(res => res.json())
      .then(d => setData(d))
      .catch(console.error);
  }, []);

  return (
    <div className="container">
      <h1>Havn</h1>
      <p style={{marginBottom: '2rem'}}>Your personal data, unified and correlated.</p>
      
      <div className="nav">
        <div className={`nav-item ${activeTab === 'insights' ? 'active' : ''}`} onClick={() => setActiveTab('insights')}>Insights Feed</div>
        <div className={`nav-item ${activeTab === 'correlate' ? 'active' : ''}`} onClick={() => setActiveTab('correlate')}>Correlate Anything</div>
        <div className={`nav-item ${activeTab === 'data' ? 'active' : ''}`} onClick={() => setActiveTab('data')}>Data Browser</div>
      </div>

      {activeTab === 'insights' && (
        <div>
          <h2>Discoveries</h2>
          {insights.length === 0 ? (
            <p>No insights generated yet. Ingest more data to see correlations.</p>
          ) : (
            <div className="grid">
              {insights.map((insight, idx) => (
                <div key={idx} className="glass-panel insight-card">
                  <div className="insight-header">
                    <h3>{insight.series1.source}.{insight.series1.name} <br/><span style={{fontSize:'0.8em', color:'var(--text-secondary)'}}>vs</span><br/> {insight.series2.source}.{insight.series2.name}</h3>
                    <div className="stat-badge">r = {insight.correlation.spearman?.r?.toFixed(2)}</div>
                  </div>
                  <p>
                    We found a statistically significant relationship (p={insight.correlation.spearman?.p_value?.toFixed(4)}) based on {insight.correlation.data_points} overlapping days.
                  </p>
                  {insight.correlation.lagged && (
                     <p className="mt-2">
                       <strong>Lagged effect:</strong> The strongest signal appears when shifting by {insight.correlation.lagged.lag_days} days.
                     </p>
                  )}
                  {insight.correlation.changepoint && (
                     <p className="mt-2">
                       <strong>Potential Shift:</strong> A simultaneous change in trends was detected around {insight.correlation.changepoint}.
                     </p>
                  )}
                  <div className="caveat">{insight.correlation.caveat}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'data' && (
        <div className="glass-panel">
          <div className="flex justify-between items-center">
            <h2>Raw Data Browser</h2>
            <p>Ingested Sources: {sources.join(', ')}</p>
          </div>
          
          <h3 className="mt-4">Recent Events</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Source</th>
                <th>Type</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {data.events.slice(0, 5).map((e, i) => (
                <tr key={i}>
                  <td>{new Date(e.timestamp).toLocaleString()}</td>
                  <td>{e.source}</td>
                  <td>{e.type}</td>
                  <td>{e.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
          
          <h3 className="mt-4" style={{marginTop: '2rem'}}>Recent Metrics</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Source</th>
                <th>Metric</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {data.metrics.slice(0, 5).map((m, i) => (
                <tr key={i}>
                  <td>{new Date(m.timestamp).toLocaleString()}</td>
                  <td>{m.source}</td>
                  <td>{m.metric_name}</td>
                  <td>{m.value} {m.unit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {activeTab === 'correlate' && (
        <div className="glass-panel">
          <h2>Correlate Anything</h2>
          <p>Manual correlation explorer coming soon. (Select two sources/metrics from dropdowns to test your own hypotheses).</p>
        </div>
      )}
    </div>
  );
}

export default App;
