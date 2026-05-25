import React, { useState } from 'react';
import './BenchmarkForm.css';

function BenchmarkForm({ onSubmit, disabled }) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [config, setConfig] = useState({
    url: 'https://google.com',
    num_requests: 30,
    concurrency: 3,
    rounds: 3,
    connect_timeout_seconds: 3,
    read_timeout_seconds: 10,
    warmup_requests: 10,
    pool_connections: 100,
    pool_maxsize: 100,
    retry_total: 1,
    retry_backoff: 0.2,
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: name === 'url' ? value : 
              name === 'retry_backoff' ? parseFloat(value) : 
              parseInt(value, 10)
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(config);
  };

  return (
    <form className="benchmark-form" onSubmit={handleSubmit}>
      
      <div className="main-config">
        <div className="form-group">
          <label htmlFor="url">Target URL</label>
          <input
            type="text"
            id="url"
            name="url"
            value={config.url}
            onChange={handleChange}
            disabled={disabled}
            placeholder="https://example.com"
            className="url-input"
          />
        </div>

        <div className="config-row">
          <div className="form-group">
            <label htmlFor="num_requests">Total Requests</label>
            <input
              type="number"
              id="num_requests"
              name="num_requests"
              value={config.num_requests}
              onChange={handleChange}
              disabled={disabled}
              min="1"
            />
          </div>

          <div className="form-group">
            <label htmlFor="concurrency">Concurrency</label>
            <input
              type="number"
              id="concurrency"
              name="concurrency"
              value={config.concurrency}
              onChange={handleChange}
              disabled={disabled}
              min="1"
            />
          </div>

          <div className="form-group">
            <label htmlFor="rounds">Rounds</label>
            <input
              type="number"
              id="rounds"
              name="rounds"
              value={config.rounds}
              onChange={handleChange}
              disabled={disabled}
              min="1"
            />
          </div>
        </div>
      </div>

      <div className="advanced-section">
        <button
          type="button"
          className="advanced-toggle"
          onClick={() => setShowAdvanced(!showAdvanced)}
          disabled={disabled}
        >
          {showAdvanced ? '▼' : '▶'} Advanced Settings
        </button>

        {showAdvanced && (
          <div className="advanced-content">
            <div className="config-row">
              <div className="form-group">
                <label htmlFor="connect_timeout_seconds">Connect Timeout (s)</label>
                <input
                  type="number"
                  id="connect_timeout_seconds"
                  name="connect_timeout_seconds"
                  value={config.connect_timeout_seconds}
                  onChange={handleChange}
                  disabled={disabled}
                  min="1"
                />
              </div>

              <div className="form-group">
                <label htmlFor="read_timeout_seconds">Read Timeout (s)</label>
                <input
                  type="number"
                  id="read_timeout_seconds"
                  name="read_timeout_seconds"
                  value={config.read_timeout_seconds}
                  onChange={handleChange}
                  disabled={disabled}
                  min="1"
                />
              </div>

              <div className="form-group">
                <label htmlFor="warmup_requests">Warmup Requests</label>
                <input
                  type="number"
                  id="warmup_requests"
                  name="warmup_requests"
                  value={config.warmup_requests}
                  onChange={handleChange}
                  disabled={disabled}
                  min="0"
                />
              </div>
            </div>

            <div className="config-row">
              <div className="form-group">
                <label htmlFor="retry_total">Max Retries</label>
                <input
                  type="number"
                  id="retry_total"
                  name="retry_total"
                  value={config.retry_total}
                  onChange={handleChange}
                  disabled={disabled}
                  min="0"
                />
              </div>

              <div className="form-group">
                <label htmlFor="retry_backoff">Retry Backoff</label>
                <input
                  type="number"
                  id="retry_backoff"
                  name="retry_backoff"
                  value={config.retry_backoff}
                  onChange={handleChange}
                  disabled={disabled}
                  step="0.1"
                  min="0"
                />
              </div>

              <div className="form-group">
                <label htmlFor="pool_connections">Pool Connections</label>
                <input
                  type="number"
                  id="pool_connections"
                  name="pool_connections"
                  value={config.pool_connections}
                  onChange={handleChange}
                  disabled={disabled}
                  min="1"
                />
              </div>
            </div>

            <div className="config-row">
              <div className="form-group">
                <label htmlFor="pool_maxsize">Pool Max Size</label>
                <input
                  type="number"
                  id="pool_maxsize"
                  name="pool_maxsize"
                  value={config.pool_maxsize}
                  onChange={handleChange}
                  disabled={disabled}
                  min="1"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      <button type="submit" disabled={disabled} className="submit-btn">
        {disabled ? '⏱ Running Benchmark...' : '▶ Start Benchmark'}
      </button>
    </form>
  );
}

export default BenchmarkForm;
