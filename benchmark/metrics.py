import math
import statistics
from typing import Any, Dict, List

from worker import RequestResult


def _percentile(values: List[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    sorted_values = sorted(values)
    rank = (len(sorted_values) - 1) * (percentile_value / 100)
    lower_index = math.floor(rank)
    upper_index = math.ceil(rank)
    if lower_index == upper_index:
        return sorted_values[lower_index]
    weight = rank - lower_index
    return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight


def calculate_metrics(results: List[RequestResult], total_time: float) -> Dict[str, Any]:
    total_requests = len(results)
    successful_results = [item for item in results if item.success]
    failed_results = [item for item in results if not item.success]
    latencies = [item.elapsed for item in results]
    queue_delays = [item.queue_delay for item in results]
    end_to_end_latencies = [item.total_elapsed for item in results]

    throughput_total = total_requests / total_time if total_time > 0 else 0.0
    throughput_success = len(successful_results) / total_time if total_time > 0 else 0.0
    average_response = statistics.mean(latencies) if latencies else 0.0
    median_response = statistics.median(latencies) if latencies else 0.0
    p95_response = _percentile(latencies, 95)
    p99_response = _percentile(latencies, 99)
    average_queue_delay = statistics.mean(queue_delays) if queue_delays else 0.0
    p95_queue_delay = _percentile(queue_delays, 95)
    average_end_to_end = statistics.mean(end_to_end_latencies) if end_to_end_latencies else 0.0
    p95_end_to_end = _percentile(end_to_end_latencies, 95)

    status_counts: Dict[int, int] = {}
    for item in successful_results:
        if item.status_code is None:
            continue
        status_counts[item.status_code] = status_counts.get(item.status_code, 0) + 1

    error_counts: Dict[str, int] = {}
    for item in failed_results:
        error_key = item.error if item.error else "UnknownError"
        error_counts[error_key] = error_counts.get(error_key, 0) + 1

    return {
        "total_time": total_time,
        "total_requests": total_requests,
        "successful_requests": len(successful_results),
        "failed_requests": len(failed_results),
        "success_rate": (len(successful_results) / total_requests) if total_requests > 0 else 0.0,
        "throughput_total": throughput_total,
        "throughput_success": throughput_success,
        "average_response": average_response,
        "median_response": median_response,
        "p95_response": p95_response,
        "p99_response": p99_response,
        "average_queue_delay": average_queue_delay,
        "p95_queue_delay": p95_queue_delay,
        "average_end_to_end": average_end_to_end,
        "p95_end_to_end": p95_end_to_end,
        "status_counts": status_counts,
        "error_counts": error_counts,
    }
