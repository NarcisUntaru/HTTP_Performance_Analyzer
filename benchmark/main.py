import time

from concurrent.futures import ThreadPoolExecutor

from config import (
    CONNECT_TIMEOUT_SECONDS,
    CONCURRENCY,
    NUM_REQUESTS,
    POOL_CONNECTIONS,
    POOL_MAXSIZE,
    READ_TIMEOUT_SECONDS,
    RETRY_BACKOFF,
    RETRY_TOTAL,
    ROUNDS,
    URL,
    WARMUP_REQUESTS,
)
from metrics import calculate_metrics

from worker import (
    configure_http_client,
    get_max_active_requests,
    make_request,
    reset_activity_metrics,
)


class Benchmark:
    def __init__(
        self,
        url: str,
        num_requests: int,
        concurrency: int,
        connect_timeout_seconds: int,
        read_timeout_seconds: int,
        warmup_requests: int,
        rounds: int,
        pool_connections: int,
        pool_maxsize: int,
        retry_total: int,
        retry_backoff: float,
    ):
        self.url = url
        self.num_requests = num_requests
        self.concurrency = concurrency
        self.connect_timeout_seconds = connect_timeout_seconds
        self.read_timeout_seconds = read_timeout_seconds
        self.warmup_requests = warmup_requests
        self.rounds = rounds
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize
        self.retry_total = retry_total
        self.retry_backoff = retry_backoff
        self.round_metrics = []
        self.aggregate_metrics = {}

    def _run_requests(self, executor: ThreadPoolExecutor, count: int):
        futures = []
        for _ in range(count):
            submit_time = time.perf_counter()
            future = executor.submit(
                make_request,
                self.url,
                self.connect_timeout_seconds,
                self.read_timeout_seconds,
                submit_time,
            )
            futures.append(future)
        return [future.result() for future in futures]

    def warmup(self, executor: ThreadPoolExecutor) -> None:
        if self.warmup_requests <= 0:
            return
        self._run_requests(executor, self.warmup_requests)

    def run_once(self, executor: ThreadPoolExecutor) -> dict:
        reset_activity_metrics()
        start_total = time.perf_counter()
        results = self._run_requests(executor, self.num_requests)
        end_total = time.perf_counter()
        total_time = end_total - start_total
        round_metrics = calculate_metrics(results, total_time)
        max_active_requests = get_max_active_requests()
        saturation = max_active_requests / self.concurrency if self.concurrency > 0 else 0.0
        round_metrics["max_active_requests"] = max_active_requests
        round_metrics["concurrency_saturation"] = saturation
        return {
            "metrics": round_metrics,
            "results": results,
            "total_time": total_time,
        }

    def run(self) -> None:
        configure_http_client(
            self.pool_connections,
            self.pool_maxsize,
            self.retry_total,
            self.retry_backoff,
        )

        self.round_metrics = []
        all_results = []
        aggregate_total_time = 0.0

        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            self.warmup(executor)

            for round_index in range(self.rounds):
                run_data = self.run_once(executor)
                round_result = run_data["metrics"]
                round_result["round"] = round_index + 1
                self.round_metrics.append(round_result)
                all_results.extend(run_data["results"])
                aggregate_total_time += run_data["total_time"]

        self.aggregate_metrics = calculate_metrics(all_results, aggregate_total_time)
        aggregate_max_active = 0
        for round_result in self.round_metrics:
            if round_result["max_active_requests"] > aggregate_max_active:
                aggregate_max_active = round_result["max_active_requests"]
        self.aggregate_metrics["max_active_requests"] = aggregate_max_active
        self.aggregate_metrics["concurrency_saturation"] = (
            aggregate_max_active / self.concurrency if self.concurrency > 0 else 0.0
        )

    def _print_report(self, title: str, results: dict) -> None:
        print(title)
        print(f"Total time: {results['total_time']:.2f}s")
        print(
            f"Requests: total={results['total_requests']} success={results['successful_requests']} failed={results['failed_requests']}"
        )
        print(f"Success rate: {results['success_rate'] * 100:.2f}%")
        print(f"Throughput total: {results['throughput_total']:.2f} req/s")
        print(f"Throughput success: {results['throughput_success']:.2f} req/s")
        print(f"Average response: {results['average_response']:.4f}s")
        print(f"Median response: {results['median_response']:.4f}s")
        print(f"P95 response: {results['p95_response']:.4f}s")
        print(f"P99 response: {results['p99_response']:.4f}s")
        print(f"Average queue delay: {results['average_queue_delay']:.4f}s")
        print(f"P95 queue delay: {results['p95_queue_delay']:.4f}s")
        print(f"Average end-to-end: {results['average_end_to_end']:.4f}s")
        print(f"P95 end-to-end: {results['p95_end_to_end']:.4f}s")
        print(f"Max active requests: {results['max_active_requests']}")
        print(f"Concurrency saturation: {results['concurrency_saturation'] * 100:.2f}%")
        print(f"Status counts: {results['status_counts']}")
        print(f"Error counts: {results['error_counts']}")

    def report(self) -> None:
        print(f"URL: {self.url}")
        print(f"Concurrency: {self.concurrency}")
        print(f"Requests per round: {self.num_requests}")
        print(f"Warm-up requests: {self.warmup_requests}")
        print(f"Rounds: {self.rounds}")
        print(
            f"Timeouts: connect={self.connect_timeout_seconds}s read={self.read_timeout_seconds}s"
        )
        print(f"Retries: total={self.retry_total} backoff={self.retry_backoff}")
        print(f"HTTP pool: connections={self.pool_connections} maxsize={self.pool_maxsize}")
        print()

        for round_result in self.round_metrics:
            self._print_report(f"Round {round_result['round']}", round_result)
            print()

        self._print_report("Aggregate", self.aggregate_metrics)


def main() -> None:
    benchmark = Benchmark(
        url=URL,
        num_requests=NUM_REQUESTS,
        concurrency=CONCURRENCY,
        connect_timeout_seconds=CONNECT_TIMEOUT_SECONDS,
        read_timeout_seconds=READ_TIMEOUT_SECONDS,
        warmup_requests=WARMUP_REQUESTS,
        rounds=ROUNDS,
        pool_connections=POOL_CONNECTIONS,
        pool_maxsize=POOL_MAXSIZE,
        retry_total=RETRY_TOTAL,
        retry_backoff=RETRY_BACKOFF,
    )
    benchmark.run()
    benchmark.report()



if __name__ == "__main__":
    main()
