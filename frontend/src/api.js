import axios from 'axios';

const API_URL = 'http://localhost:5001/api';

export const runBenchmark = async (config, signal, onProgress) => {
  try {
    // Start the benchmark
    await axios.post(`${API_URL}/benchmark`, config, { signal });
    
    // Immediately start polling for progress
    let polling = true;
    let finalResults = null;
    while (polling) {
      try {
        const progressResponse = await axios.get(`${API_URL}/progress`);
        if (onProgress && progressResponse.data) {
          onProgress(progressResponse.data);
        }
        if (!progressResponse.data.running) {
          // Benchmark completed, get final results
          finalResults = progressResponse.data;
          polling = false;
          break;
        }
        await new Promise(resolve => setTimeout(resolve, 500));
      } catch (err) {
        if (err.code === 'ECONNABORTED') {
          polling = false;
          break;
        }
        // Continue polling even if there's a minor error
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
    
    return {
      success: true,
      aggregate_metrics: finalResults?.aggregate_metrics,
      round_metrics: finalResults?.round_metrics
    };
  } catch (error) {
    if (error.code === 'ECONNABORTED') {
      throw new Error('Benchmark cancelled');
    }
    throw error;
  }
};

export const cancelBenchmark = async () => {
  try {
    const response = await axios.post(`${API_URL}/cancel`);
    return response.data;
  } catch (error) {
    console.error('Failed to cancel benchmark:', error);
    throw error;
  }
};

export const checkHealth = async () => {
  const response = await axios.get(`${API_URL}/health`);
  return response.data;
};
