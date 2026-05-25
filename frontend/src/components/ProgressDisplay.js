import React, { useMemo } from 'react';
import './ProgressDisplay.css';

function ProgressDisplay({ progress }) {
  const currentRound = progress.current_round || 0;
  const totalRounds = progress.total_rounds || 0;
  const status = progress.status || 'initializing';

  const rounds = useMemo(() => {
    const roundsList = [];
    for (let i = 1; i <= totalRounds; i++) {
      if (i < currentRound) {
        roundsList.push({
          number: i,
          completed: true,
          running: false,
          info: progress.rounds[i - 1] || {}
        });
      } else if (i === currentRound && status !== 'completed' && status !== 'cancelled') {
        roundsList.push({
          number: i,
          completed: false,
          running: true,
          info: progress.rounds[i - 1] || {}
        });
      } else if (i === currentRound && (status === 'completed' || status === 'cancelled')) {
        // Last round completed
        roundsList.push({
          number: i,
          completed: true,
          running: false,
          info: progress.rounds[i - 1] || {}
        });
      } else {
        roundsList.push({
          number: i,
          completed: false,
          running: false,
          info: {}
        });
      }
    }
    return roundsList;
  }, [currentRound, totalRounds, progress.rounds, status]);

  return (
    <div className="progress-display">
      <div className="progress-header">
        <h3>Benchmark Progress</h3>
        <div className="progress-stats">
          <span className="progress-stat">Round {currentRound} of {totalRounds}</span>
          <span className={`progress-stat status-${status}`}>{status}</span>
        </div>
      </div>

      <div className="rounds-container">
        {rounds.map((round, idx) => (
          <div key={idx} className={`round-item ${round.completed ? 'completed' : round.running ? 'running' : 'pending'}`}>
            <div className="round-header">
              <span className="round-number">Round {round.number}</span>
              {round.completed && <span className="checkmark">✓</span>}
              {round.running && <span className="running-indicator"></span>}
            </div>
            {round.info && Object.keys(round.info).length > 0 && (
              <div className="round-info">
                {round.info.throughput_total !== undefined && (
                  <div className="info-item">
                    <span className="label">Throughput:</span>
                    <span className="value">{round.info.throughput_total.toFixed(2)} req/s</span>
                  </div>
                )}
                {round.info.average_response !== undefined && (
                  <div className="info-item">
                    <span className="label">Avg Response:</span>
                    <span className="value">{(round.info.average_response * 1000).toFixed(2)} ms</span>
                  </div>
                )}
                {round.info.success_rate !== undefined && (
                  <div className="info-item">
                    <span className="label">Success Rate:</span>
                    <span className="value">{(round.info.success_rate * 100).toFixed(1)}%</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="overall-progress">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${(currentRound / totalRounds) * 100}%` }}></div>
        </div>
        <span className="progress-percentage">{Math.round((currentRound / totalRounds) * 100)}%</span>
      </div>
    </div>
  );
}

export default ProgressDisplay;
