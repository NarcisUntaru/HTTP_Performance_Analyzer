import React, { useState, useRef } from 'react';
import { runBenchmark, cancelBenchmark } from './api';
import BenchmarkForm from './components/BenchmarkForm';
import ResultsDisplay from './components/ResultsDisplay';
import ProgressDisplay from './components/ProgressDisplay';
import './App.css';

function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(null);
  const [benchmarkUrl, setBenchmarkUrl] = useState(null);
  const abortControllerRef = useRef(null);

  const handleBenchmark = async (config) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setProgress(null);
    setBenchmarkUrl(config.url);
    abortControllerRef.current = new AbortController();
    
    try {
      const data = await runBenchmark(config, abortControllerRef.current.signal, setProgress);
      if (data && data.success) {
        setResults(data);
      } else if (data) {
        setError(data.error || 'Failed to run benchmark');
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Error connecting to API');
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = async () => {
    if (abortControllerRef.current) {
      // Signal backend to stop
      try {
        await cancelBenchmark();
      } catch (err) {
        console.error('Error cancelling benchmark:', err);
      }
      
      // Abort frontend polling
      abortControllerRef.current.abort();
      setLoading(false);
      setError('Benchmark cancelled by user');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>LatencyLens</h1>
      </header>
      
      <div className="app-container">
        <div className="form-section">
          <BenchmarkForm onSubmit={handleBenchmark} disabled={loading} />
          {loading && <button className="stop-btn" onClick={handleStop}>Stop Benchmark</button>}
        </div>
        
        {loading && progress && <ProgressDisplay progress={progress} />}
        {results && <ResultsDisplay results={results} url={benchmarkUrl} />}
      </div>
    </div>
  );
}

export default App;
