"""Definition of the MQTBenchmark wrapper."""

from __future__ import annotations

import contextlib
from functools import cached_property
from typing import TYPE_CHECKING

from mqt.bench import get_benchmark_indep

from graphix_mqtbench._benchmark_names import BenchmarkName
from graphix_mqtbench.converter import qiskit_to_graphix_circuit

if TYPE_CHECKING:
    from graphix.pattern import Pattern
    from graphix.transpiler import Circuit
    from qiskit import QiskitCircuit


class MQTBenchmark:
    """A wrapper around MQT Bench quantum circuits for benchmarking purposes.

    Retrieves a named benchmark circuit for a given qubit count and exposes
    it as a raw Qiskit circuit, and a Graphix circuit and pattern.

    Parameters
    ----------
    name : BenchmarkName
        The benchmark algorithm to instantiate.
    nqubits : int
        Number of qubits for the benchmark circuit.
    **kwargs
        Additional keyword arguments forwarded to :func:`mqt.bench.get_benchmark_indep`.

    Raises
    ------
    BenchmarkError
        If the requested benchmark does not exist for the given qubit count.

    Notes
    -----
    The raw Qiskit circuit from ``mqt.bench`` may include a terminal measurement segment, which is omitted from circuit as Graphix does not yet support classical registers. The circuit is also transpiled via :func:`qiskit.transpiler` into the gate set supported by Graphix, which may increase the gate count.

    Examples
    --------
    >>> bench = MQTBenchmark(BenchmarkName.QFT, nqubits=4)
    >>> bench.name
    <BenchmarkName.QFT: 'qft'>
    >>> bench.nqubits
    4
    """

    def __init__(self, name: BenchmarkName, nqubits: int, **kwargs) -> None:
        self._name = name
        self._nqubits = nqubits
        self._kwargs = kwargs
        try:
            self._raw_circuit = get_benchmark_indep(benchmark=name.value, circuit_size=nqubits, **kwargs)
        except Exception as e:
            # If a benchmark does not exist for a given number of qubits, it may raise several
            # different types of exceptions so we use a catch-all `Exception`.
            raise BenchmarkError(f"{name.value} benchmark does not exist for {nqubits} qubits.") from e

    def __repr__(self) -> str:
        """Return an unambiguous string representation of the benchmark.

        Returns
        -------
        str
        """
        kwargs_str = (", " + ", ".join(f"{k}={v!r}" for k, v in self._kwargs.items())) if self._kwargs else ""
        return f"MQTBenchmark(name={self._name}, nqubits={self._nqubits}{kwargs_str})"

    @property
    def name(self) -> BenchmarkName:
        """The benchmark algorithm name.

        Returns
        -------
        BenchmarkName
            Enum member identifying the benchmark.
        """
        return self._name

    @property
    def nqubits(self) -> int:
        """The number of qubits in the benchmark circuit.

        Returns
        -------
        int
            Qubit count passed at construction.
        """
        return self._nqubits

    @property
    def raw_circuit(self) -> QiskitCircuit:
        """Target-independent raw Qiskit circuit for this benchmark.

        Prefer ``circuit`` for downstream Graphix work; this property
        exposes the underlying backend representation for interoperability.

        Returns
        -------
        QiskitCircuit
            Circuit as returned by :func:`mqt.bench.get_benchmark_indep`.
        """
        return self._raw_circuit

    @cached_property
    def circuit(self) -> Circuit:
        """The benchmark circuit converted to a Graphix :class:`graphix.transpiler.Circuit.

        Computed once and cached on first access.

        Returns
        -------
        Circuit
            Graphix circuit for the benchmark.
        """
        return qiskit_to_graphix_circuit(self._raw_circuit)

    @cached_property
    def pattern(self) -> Pattern:
        """The MBQC pattern derived from the benchmark circuit.

        Transpiles ``circuit`` to a class:`graphix.pattern.Pattern` with default transpiler
        and caches the result.

        Returns
        -------
        Pattern
            MBQC pattern corresponding to ``circuit``.
        """
        return self.circuit.transpile().pattern


def generate_benchmarks(nqubits: int, **kwargs) -> tuple[MQTBenchmark, ...]:
    """Generate a sequence of all MQT benchmarks with a given number of qubits.

    If a given benchmark does not exist for ``nqubits``, it is skipped.

    Parameters
    ----------
    nqubits : int
        Number of qubits
    **kwargs
        Additional keyword arguments forwarded to :func:`mqt.bench.get_benchmark_indep`.

    Returns
    -------
    tuple[MQTBenchmark, ...]
    """
    benchmarks: list[MQTBenchmark] = []
    for bench in BenchmarkName:
        with contextlib.suppress(BenchmarkError):
            benchmarks.append(MQTBenchmark(bench, nqubits, **kwargs))
    return tuple(benchmarks)


class BenchmarkError(Exception):
    """Exception subclass to handle benchmark errors."""
