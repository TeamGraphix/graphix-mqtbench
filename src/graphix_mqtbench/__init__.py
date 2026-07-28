"""A wrapper around MQT Bench quantum circuits for benchmarking purposes."""

from graphix_mqtbench._benchmark_names import BenchmarkName
from graphix_mqtbench.benchmark import MQTBenchmark, generate_benchmarks

__all__ = ["MQTBenchmark", "BenchmarkName", "generate_benchmarks"]