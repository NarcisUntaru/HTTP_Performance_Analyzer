from flask import Flask, request, jsonify, make_response, Response
from main import Benchmark
import traceback
import json
import threading
import time

app = Flask(__name__)
benchmark_state = {
    'running': False,
    'current_round': 0,
    'total_rounds': 0,
    'rounds': [],
    'status': 'idle',
    'cancelled': False
}
state_lock = threading.Lock()

def run_benchmark_in_background(data):
    """Run benchmark in a background thread and update shared state"""
    try:
        url = data.get('url', 'https://httpbin.org/delay/1')
        num_requests = int(data.get('num_requests', 100))
        concurrency = int(data.get('concurrency', 3))
        connect_timeout_seconds = int(data.get('connect_timeout_seconds', 3))
        read_timeout_seconds = int(data.get('read_timeout_seconds', 10))
        warmup_requests = int(data.get('warmup_requests', 10))
        rounds = int(data.get('rounds', 3))
        pool_connections = int(data.get('pool_connections', 100))
        pool_maxsize = int(data.get('pool_maxsize', 100))
        retry_total = int(data.get('retry_total', 1))
        retry_backoff = float(data.get('retry_backoff', 0.2))
        
        with state_lock:
            benchmark_state['running'] = True
            benchmark_state['current_round'] = 0
            benchmark_state['total_rounds'] = rounds
            benchmark_state['rounds'] = []
            benchmark_state['status'] = 'warmup'
            benchmark_state['cancelled'] = False
        
        benchmark = Benchmark(
            url=url,
            num_requests=num_requests,
            concurrency=concurrency,
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
            warmup_requests=warmup_requests,
            rounds=rounds,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            retry_total=retry_total,
            retry_backoff=retry_backoff,
        )
        
        from concurrent.futures import ThreadPoolExecutor
        from worker import configure_http_client, reset_activity_metrics, get_max_active_requests, make_request
        from metrics import calculate_metrics
        
        configure_http_client(
            pool_connections,
            pool_maxsize,
            retry_total,
            retry_backoff,
        )
        
        benchmark.round_metrics = []
        all_results = []
        aggregate_total_time = 0.0
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            benchmark.warmup(executor)
            
            # Check if cancelled before proceeding
            with state_lock:
                if benchmark_state['cancelled']:
                    benchmark_state['running'] = False
                    benchmark_state['status'] = 'cancelled'
                    return
                benchmark_state['status'] = 'running'
            
            for round_index in range(rounds):
                # Check if cancelled before each round
                with state_lock:
                    if benchmark_state['cancelled']:
                        benchmark_state['running'] = False
                        benchmark_state['status'] = 'cancelled'
                        return
                reset_activity_metrics()
                start_total = time.perf_counter()
                
                futures = []
                for _ in range(num_requests):
                    submit_time = time.perf_counter()
                    future = executor.submit(
                        make_request,
                        url,
                        connect_timeout_seconds,
                        read_timeout_seconds,
                        submit_time,
                    )
                    futures.append(future)
                
                results = [future.result() for future in futures]
                end_total = time.perf_counter()
                total_time = end_total - start_total
                
                round_metrics = calculate_metrics(results, total_time)
                max_active_requests = get_max_active_requests()
                saturation = max_active_requests / concurrency if concurrency > 0 else 0.0
                round_metrics["max_active_requests"] = max_active_requests
                round_metrics["concurrency_saturation"] = saturation
                round_metrics["round"] = round_index + 1
                
                benchmark.round_metrics.append(round_metrics)
                all_results.extend(results)
                aggregate_total_time += total_time
                
                # Update shared state after each round completes
                with state_lock:
                    benchmark_state['current_round'] = round_index + 1
                    benchmark_state['rounds'].append({
                        'number': round_index + 1,
                        'throughput_total': round_metrics.get('throughput_total', 0),
                        'average_response': round_metrics.get('average_response', 0),
                        'success_rate': round_metrics.get('success_rate', 0),
                    })
                    if benchmark_state['cancelled']:
                        benchmark_state['running'] = False
                        benchmark_state['status'] = 'cancelled'
                        return
        
        benchmark.aggregate_metrics = calculate_metrics(all_results, aggregate_total_time)
        aggregate_max_active = 0
        for round_result in benchmark.round_metrics:
            if round_result["max_active_requests"] > aggregate_max_active:
                aggregate_max_active = round_result["max_active_requests"]
        benchmark.aggregate_metrics["max_active_requests"] = aggregate_max_active
        benchmark.aggregate_metrics["concurrency_saturation"] = (
            aggregate_max_active / concurrency if concurrency > 0 else 0.0
        )
        
        with state_lock:
            benchmark_state['running'] = False
            benchmark_state['current_round'] = rounds
            benchmark_state['status'] = 'completed'
            # Store results for later retrieval
            benchmark_state['aggregate_metrics'] = benchmark.aggregate_metrics
            benchmark_state['round_metrics'] = benchmark.round_metrics
            
    except Exception as e:
        traceback.print_exc()
        with state_lock:
            benchmark_state['running'] = False
            benchmark_state['status'] = 'error'

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        response = make_response()
    else:
        response = make_response(jsonify({'status': 'ok'}))
    
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/benchmark', methods=['POST', 'OPTIONS'])
def run_benchmark():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        data = request.json
        
        # Start benchmark in background thread
        thread = threading.Thread(target=run_benchmark_in_background, args=(data,), daemon=True)
        thread.start()
        
        response = make_response(jsonify({'success': True, 'message': 'Benchmark started'}))
    except Exception as e:
        traceback.print_exc()
        response = make_response(jsonify({
            'success': False,
            'error': str(e),
        }), 400)
    
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/progress', methods=['GET'])
def get_progress():
    with state_lock:
        progress = {
            'running': benchmark_state['running'],
            'current_round': benchmark_state['current_round'],
            'total_rounds': benchmark_state['total_rounds'],
            'rounds': benchmark_state['rounds'],
            'status': benchmark_state['status'],
            'aggregate_metrics': benchmark_state.get('aggregate_metrics'),
            'round_metrics': benchmark_state.get('round_metrics')
        }
    
    response = make_response(jsonify(progress))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/api/cancel', methods=['POST', 'OPTIONS'])
def cancel_benchmark():
    if request.method == 'OPTIONS':
        response = make_response()
    else:
        with state_lock:
            benchmark_state['cancelled'] = True
        response = make_response(jsonify({'success': True, 'message': 'Cancellation requested'}))
    
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
