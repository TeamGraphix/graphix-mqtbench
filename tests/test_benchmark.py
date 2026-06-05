from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pytest
from graphix.states import BasicStates
from mqt.bench.benchmarks import get_available_benchmark_names
from qiskit.primitives import StatevectorSampler

from graphix_mqtbench import BenchmarkName, MQTBenchmark, generate_benchmarks

if TYPE_CHECKING:
    from numpy.random import Generator


def simulate_benchmark(
    bench: MQTBenchmark, shots: int, seed: int, rng: Generator
) -> tuple[dict[str, float], dict[str, float]]:
    qc_qiskit = bench.raw_circuit
    # We remove all measurements and measure again because not all qubits are measured in circuits of the benchmark suite.
    qc_qiskit.remove_final_measurements()
    qc_qiskit.measure_all()
    sampler = StatevectorSampler(seed=seed)
    creg_name = qc_qiskit.cregs[0].name
    result = sampler.run([qc_qiskit], shots=shots).result()[0].data
    counts_qiskit = getattr(result, creg_name).get_counts()

    # Transpiles benchmark to graphix circuit and then to pattern
    prob_graphix = bench.pattern.simulate_pattern(input_state=BasicStates.ZERO, rng=rng).to_prob_dict(encoding="LSB")

    return counts_qiskit, prob_graphix


class TestMQTBenchmark:
    SHOTS = 8096
    SEED = 24
    ERR = 0.02

    @pytest.mark.parametrize(
        "test_case",
        [bench for nqubits in (2, 3, 4) for bench in generate_benchmarks(nqubits=nqubits)],
    )
    def test_qiskit_simulation(self, test_case: MQTBenchmark, fx_rng: Generator) -> None:
        counts_qiskit, prob_graphix = simulate_benchmark(test_case, self.SHOTS, self.SEED, fx_rng)

        for key, value in counts_qiskit.items():
            assert math.isclose(prob_graphix[key], value / self.SHOTS, rel_tol=0, abs_tol=self.ERR)

    def test_init(self) -> None:
        bench = MQTBenchmark(BenchmarkName.QFT, 3, generate_mirror_circuit=True, random_parameters=True)
        r = repr(bench)
        assert "BenchmarkName.QFT" in r
        assert "nqubits=3" in r
        assert "generate_mirror_circuit=True" in r
        assert "random_parameters=True" in r

    def test_benchmark_names(self) -> None:
        names = get_available_benchmark_names()
        for name, bench in zip(names, BenchmarkName, strict=True):
            assert name.upper() == bench.name
            assert name == bench.value
