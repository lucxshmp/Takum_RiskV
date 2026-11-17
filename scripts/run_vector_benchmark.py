import csv
import random
import sys
from pathlib import Path

import mpmath as mp

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from takum.simulator import VectorMachine
from takum.benchmark import run_benchmark
from takum.metrics import calculate_high_precision_metrics


def generate_vectors(size, seed=42):
    """Gera dois vetores determinísticos."""
    rng = random.Random(seed)

    a = [rng.uniform(-0.1, 0.1) for _ in range(size)]
    b = [rng.uniform(-0.1, 0.1) for _ in range(size)]

    return a, b


def calculate_reference(operation, a, b):
    """Calcula a referência com precisão ampliada."""

    with mp.workdps(50):
        a_mp = [mp.mpf(str(x)) for x in a]
        b_mp = [mp.mpf(str(x)) for x in b]

        if operation == "vtadd.vv":
            return [x + y for x, y in zip(a_mp, b_mp)]

        if operation == "vtsub.vv":
            return [x - y for x, y in zip(a_mp, b_mp)]

        if operation == "vtmul.vv":
            return [x * y for x, y in zip(a_mp, b_mp)]

        if operation == "vtdot.vv":
            result = sum(
                (x * y for x, y in zip(a_mp, b_mp)),
                mp.mpf("0")
            )
            return [result]

    raise ValueError(f"Operação desconhecida: {operation}")


def run_experiment(vl, sew, operation, repetitions=100):
    """Executa e avalia uma operação vetorial."""

    machine = VectorMachine(max_vl=256)
    machine.configure(vl=vl, sew=sew)

    a, b = generate_vectors(vl)

    machine.load_vector("v1", a)
    machine.load_vector("v2", b)

    # Usa os valores efetivamente representados em Takum.
    represented_a = machine.read_vector("v1")
    represented_b = machine.read_vector("v2")

    reference = calculate_reference(
        operation,
        represented_a,
        represented_b
    )

    def execute_operation():
        return machine.execute(
            instruction=operation,
            vd="v3",
            vs1="v1",
            vs2="v2"
        )

    timing = run_benchmark(
        execute_operation,
        repetitions=repetitions
    )

    measured = timing["result"]

    metrics = calculate_high_precision_metrics(
        reference,
        measured
    )

    statistics = machine.get_statistics()

    return {
        "vl": vl,
        "sew": sew,
        "operation": operation,
        "repetitions": repetitions,
        "total_time": timing["total_time"],
        "average_time": timing["average_time"],
        "instructions_executed": statistics["instructions_executed"],
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "max_error": metrics["max_error"],
        "mean_relative_error": metrics["mean_relative_error"],
        "p95_relative_error": metrics["p95_relative_error"],
    }


def main():
    output_dir = PROJECT_ROOT / "results"
    output_dir.mkdir(exist_ok=True)

    operations = [
        "vtadd.vv",
        "vtsub.vv",
        "vtmul.vv",
        "vtdot.vv",
    ]

    vector_lengths = [8]
    widths = [8, 16, 32]

    repetitions = 1
    results = []

    for width in widths:
        for vl in vector_lengths:
            for operation in operations:

                print(
                    f"Executando {operation} | "
                    f"T{width} | VL={vl}"
                )

                result = run_experiment(
                    vl=vl,
                    sew=width,
                    operation=operation,
                    repetitions=repetitions
                )

                results.append(result)

    output_file = output_dir / "vector_benchmark.csv"

    fields = list(results[0].keys())

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    print("\nExperimento concluído.")
    print(f"Total de configurações: {len(results)}")
    print(f"Resultados salvos em: {output_file}")


if __name__ == "__main__":
    main()