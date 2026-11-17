
"""
Rotinas de benchmark para operações Takum.

Mede o tempo de execução de operações vetoriais em software.
Não representa desempenho de instruções RVV em hardware.
"""

from time import perf_counter
from typing import Callable, Dict, List, Any


def run_benchmark(
    operation: Callable,
    *args,
    repetitions: int = 1000,
    **kwargs
) -> Dict[str, Any]:
    """
    Executa uma operação repetidamente e mede seu tempo.

    Retorna:
        repetitions: número de execuções
        total_time: tempo total em segundos
        average_time: tempo médio por execução
        result: resultado da última execução
    """
    if repetitions <= 0:
        raise ValueError("repetitions deve ser maior que zero")

    result = None

    start = perf_counter()

    for _ in range(repetitions):
        result = operation(*args, **kwargs)

    end = perf_counter()

    total_time = end - start

    return {
        "repetitions": repetitions,
        "total_time": total_time,
        "average_time": total_time / repetitions,
        "result": result,
    }


def print_benchmark(results: Dict[str, Any]) -> None:
    """Exibe os resultados do benchmark."""
    print("===== BENCHMARK =====")
    print(f"Execuções: {results['repetitions']}")
    print(f"Tempo total: {results['total_time']:.8f} s")
    print(f"Tempo médio: {results['average_time']:.8e} s")
    print("=====================")
