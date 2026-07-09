from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from graphix import BasicStates, Statevec
from mqt.bench.benchmarks import get_available_benchmark_names
from qiskit.converters import circuit_to_dag, dag_to_circuit  # type: ignore[attr-defined]
from qiskit.quantum_info.states.statevector import Statevector as Statevector_qiskit

from graphix_mqtbench import BenchmarkName, MQTBenchmark, generate_benchmarks

if TYPE_CHECKING:
    from numpy.random import Generator


def verify_benchmark(bench: MQTBenchmark, rng: Generator) -> bool:
    qc_qiskit = bench.raw_circuit

    # Some benchmarks are given with measurements at the end.
    # We remove them to obtain a statevector.
    # Clear the layout before removing measurements to avoid qiskit warnings.
    qc_clean = dag_to_circuit(circuit_to_dag(qc_qiskit))  # type: ignore[no-untyped-call]
    qc_clean.remove_final_measurements()
    qiskit_data = Statevector_qiskit(qc_clean).data  # numpy array of complex amplitudes

    perm = list(reversed(range(bench.nqubits)))
    qiskit_data_msb = qiskit_data.reshape((2,) * bench.nqubits).transpose(perm).reshape(-1)
    sv_ref = Statevec(qiskit_data_msb)

    # Transpiles benchmark to graphix circuit and then to pattern.
    pattern = bench.pattern.minimize_space()
    sv_test = pattern.simulate_pattern(input_state=BasicStates.ZERO, rng=rng)

    return sv_ref.isclose(sv_test)
    return True


class TestMQTBenchmark:
    @pytest.mark.parametrize(
        "test_case",
        [bench for nqubits in (2, 3, 4) for bench in generate_benchmarks(nqubits=nqubits)],
    )
    def test_qiskit_simulation(self, test_case: MQTBenchmark, fx_rng: Generator) -> None:
        assert verify_benchmark(test_case, fx_rng)

    def test_init(self) -> None:
        bench = MQTBenchmark(BenchmarkName.QFT, 3, generate_mirror_circuit=False, random_parameters=True)
        r = repr(bench)
        # Python==3.10 -> 'MQTBenchmark(name=qft, nqubits=3...'
        # Python>=3.11 -> 'MQTBenchmark(name=BenchmarkName.QFT, nqubits=3...'
        assert "BenchmarkName.QFT" in r or "qft" in r
        assert "nqubits=3" in r
        assert "generate_mirror_circuit=False" in r
        assert "random_parameters=True" in r

    def test_benchmark_names(self) -> None:
        names = get_available_benchmark_names()
        for name, bench in zip(names, BenchmarkName, strict=True):
            assert name.upper() == bench.name
            assert name == bench.value
