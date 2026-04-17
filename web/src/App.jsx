import React, { useState, useEffect } from 'react';
import './App.css';

const SourceCard = ({ id, stats }) => (
  <div className="card glass-card">
    <div className="card-header">
      <span className="source-badge">Active Source</span>
      <h3>{id}</h3>
    </div>
    <div className="card-grid">
      <div className="metric-box">
        <label>Throughput</label>
        <div className="value neon-text">{stats.fps} <small>FPS</small></div>
      </div>
      <div className="metric-box">
        <label>Latency</label>
        <div className="value">{stats.latency_ms} <small>ms</small></div>
      </div>
      <div className="metric-box">
        <label>Reliability</label>
        <div className="value orange-text">{stats.total_drops} <small>Drops</small></div>
      </div>
      <div className="metric-box">
        <label>Total Frames</label>
        <div className="value gray-text">{stats.total_frames}</div>
      </div>
      <div className="metric-box">
        <label>Active Humans</label>
        <div className="value neon-text">{stats.active_subjects}</div>
      </div>
      <div className="metric-box intent-box full-width">
        <label>Detected Intent</label>
        <div className="intent-badge-container">
          <span className="intent-label">{stats.current_intent}</span>
          <div className="confidence-bar">
            <div className="confidence-fill" style={{ width: `${(stats.intent_confidence * 100).toFixed(0)}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

function App() {
  const [data, setData] = useState({ metrics: {}, alerts: [], memory_usage_mb: 0, status: "Connecting..." });
  const [connected, setConnected] = useState(false);
  const [threshold, setThreshold] = useState(0.02);

  const updateThreshold = async (val) => {
    setThreshold(val);
    try {
      await fetch(`http://localhost:8000/intelligence/config?threshold=${val}`, { method: 'POST' });
    } catch (err) {
      console.error("Failed to update intelligence threshold", err);
    }
  };

  useEffect(() => {
    let ws;
    const connect = () => {
      ws = new WebSocket("ws://localhost:8000/ws/stream");
      
      ws.onopen = () => {
        setConnected(true);
        console.log("Connected to Sign-Verse Command Center");
      };
      
      ws.onmessage = (event) => {
        const report = JSON.parse(event.data);
        setData(report);
      };
      
      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000); // Auto-reconnect
      };
    };

    connect();
    return () => ws?.close();
  }, []);

  return (
    <div className="app-container">
      <header className="main-header">
        <div className="logo-section">
          <div className={`status-indicator ${connected ? 'status-online' : 'status-offline'}`}></div>
          <h1>SIGN-VERSE <small className="neon-text">ROBOTICS MONITOR</small></h1>
        </div>
        <div className="system-summary">
          <div className="summary-item">
            <label>RAM USAGE</label>
            <span>{data.memory_usage_mb} MB</span>
          </div>
          <div className="summary-item">
            <label>ENGINE STATUS</label>
            <span className="status-badge">{data.status}</span>
          </div>
          <div className="summary-item control-item">
            <label>INTENT SENSITIVITY ({threshold})</label>
            <input 
              type="range" 
              min="0.005" 
              max="0.1" 
              step="0.005" 
              value={threshold} 
              onChange={(e) => updateThreshold(parseFloat(e.target.value))} 
            />
          </div>
        </div>
      </header>

      <main className="dashboard-content">
        <section className="alerts-section">
          {data.alerts && data.alerts.length > 0 ? (
            <div className="alerts-container">
              {data.alerts.map((alert, i) => (
                <div key={i} className="alert-item">{alert}</div>
              ))}
            </div>
          ) : (
            <div className="no-alerts">SYSTEMS NOMINAL - ZERO ANOMALIES DETECTED</div>
          )}
        </section>

        <section className="sources-grid">
          {Object.entries(data.metrics || {}).map(([id, stats]) => (
            <SourceCard key={id} id={id} stats={stats} />
          ))}
        </section>
      </main>

      <footer className="main-footer">
        <div>PRODUCTION GRADE OBSERBABILITY | V2.0.0</div>
        <div>POG-1 ROBOTICS STACK</div>
      </footer>
    </div>
  );
}

export default App;
