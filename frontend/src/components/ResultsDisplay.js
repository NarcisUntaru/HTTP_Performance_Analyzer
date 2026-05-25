import React from 'react';
import html2pdf from 'html2pdf.js';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import './ResultsDisplay.css';

function ResultsDisplay({ results, url }) {
  if (!results || !results.aggregate_metrics || !results.round_metrics) {
    return <div className="results-display"><p>No results available</p></div>;
  }

  const agg = results.aggregate_metrics;
  const rounds = results.round_metrics;

  const handleExportPDF = () => {
    const element = document.getElementById('results-content');
    const opt = {
      margin: 10,
      filename: `benchmark-results-${new Date().toISOString().split('T')[0]}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { orientation: 'portrait', unit: 'mm', format: 'a4' }
    };
    html2pdf().set(opt).from(element).save();
  };

  const roundChartData = (rounds || []).map(round => ({
    round: `R${round.round}`,
    throughput: parseFloat((round.throughput_total || 0).toFixed(2)),
    avg_response: parseFloat(((round.average_response || 0) * 1000).toFixed(2)),
    p95_response: parseFloat(((round.p95_response || 0) * 1000).toFixed(2)),
    p99_response: parseFloat(((round.p99_response || 0) * 1000).toFixed(2)),
  }));

  const statusData = Object.entries(agg.status_counts || {}).map(([status, count]) => ({
    name: `${status}`,
    value: count,
  }));

  const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

  const successRate = ((agg.success_rate || 0) * 100);
  const failureRate = 100 - successRate;

  return (
    <div className="results-display">
      <div id="results-content">
        <div className="results-header">
          <h2>Benchmark Results</h2>
          {url && <div className="benchmark-url"><strong>{url}</strong></div>}
          <div className="results-meta">
            <span className="meta-item">Total Requests: <strong>{agg.total_requests || 0}</strong></span>
            <span className="meta-item">Total Time: <strong>{(agg.total_time || 0).toFixed(2)}s</strong></span>
          </div>
        </div>

        <div className="metrics-grid">
        <div className="metric-card primary">
          <div className="metric-icon check-icon">✓</div>
          <div className="metric-content">
            <div className="metric-label">Success Rate</div>
            <div className="metric-value">{successRate.toFixed(1)}%</div>
            <div className="metric-detail">{agg.successful_requests || 0} of {agg.total_requests || 0}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon bolt-icon">⚡</div>
          <div className="metric-content">
            <div className="metric-label">Throughput</div>
            <div className="metric-value">{(agg.throughput_total || 0).toFixed(2)}</div>
            <div className="metric-detail">req/s</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon clock-icon">⏱</div>
          <div className="metric-content">
            <div className="metric-label">Avg Response</div>
            <div className="metric-value">{((agg.average_response || 0) * 1000).toFixed(2)}</div>
            <div className="metric-detail">ms</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon chart-icon">📊</div>
          <div className="metric-content">
            <div className="metric-label">Median Response</div>
            <div className="metric-value">{((agg.median_response || 0) * 1000).toFixed(2)}</div>
            <div className="metric-detail">ms</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon trend-icon">📈</div>
          <div className="metric-content">
            <div className="metric-label">P95 Response</div>
            <div className="metric-value">{((agg.p95_response || 0) * 1000).toFixed(2)}</div>
            <div className="metric-detail">ms</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon alert-icon">⚠</div>
          <div className="metric-content">
            <div className="metric-label">P99 Response</div>
            <div className="metric-value">{((agg.p99_response || 0) * 1000).toFixed(2)}</div>
            <div className="metric-detail">ms</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon hourglass-icon">⏳</div>
          <div className="metric-content">
            <div className="metric-label">Avg Queue Delay</div>
            <div className="metric-value">{((agg.average_queue_delay || 0) * 1000).toFixed(2)}</div>
            <div className="metric-detail">ms</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon cycle-icon">🔄</div>
          <div className="metric-content">
            <div className="metric-label">Max Active Requests</div>
            <div className="metric-value">{agg.max_active_requests || 0}</div>
            <div className="metric-detail">concurrent</div>
          </div>
        </div>
      </div>

      {roundChartData.length > 0 && (
        <div className="chart-section">
          <div className="chart-container">
            <h3>Throughput Per Round</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={roundChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="round" stroke="#999" />
                <YAxis stroke="#999" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #e0e0e0', borderRadius: '4px' }}
                  formatter={(value) => value.toFixed(2)}
                />
                <Legend />
                <Line type="monotone" dataKey="throughput" stroke="#0066cc" strokeWidth={2} dot={{ fill: '#0066cc', r: 4 }} name="Throughput (req/s)" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Response Time Per Round</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={roundChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="round" stroke="#999" />
                <YAxis stroke="#999" />
                <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e0e0e0', borderRadius: '4px' }} />
                <Legend />
                <Bar dataKey="avg_response" fill="#10b981" name="Avg (ms)" />
                <Bar dataKey="p95_response" fill="#f59e0b" name="P95 (ms)" />
                <Bar dataKey="p99_response" fill="#ef4444" name="P99 (ms)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {statusData.length > 0 && (
        <div className="chart-section">
          <div className="chart-container">
            <h3>Status Code Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {agg.error_counts && Object.keys(agg.error_counts).length > 0 && (
        <div className="errors-section">
          <h3>Errors Detected</h3>
          <div className="error-list">
            {Object.entries(agg.error_counts).map(([error, count]) => (
              <div key={error} className="error-item">
                <div className="error-icon">!</div>
                <div className="error-info">
                  <div className="error-name">{error}</div>
                  <div className="error-count">{count} occurrence{count > 1 ? 's' : ''}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      </div>

      <div className="export-section">
        <button onClick={handleExportPDF} className="export-btn">
          Download PDF Report
        </button>
      </div>
    </div>
  );
}

export default ResultsDisplay;
