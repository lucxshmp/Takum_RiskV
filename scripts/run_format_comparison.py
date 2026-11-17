import csv
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from takum.metrics import compare_numeric_formats


def generate_near_zero_dataset(size=1000, seed=42):
    """Gera valores pequenos, próximos de zero."""
    rng = random.Random(seed)

    return [
        rng.uniform(-1e-10, 1e-10)
        for _ in range(size)
    ]


def generate_moderate_dataset(size=1000, seed=43):
    """Gera valores distribuídos em uma faixa moderada."""
    rng = random.Random(seed)

    return [
        rng.uniform(-100, 100)
        for _ in range(size)
    ]


def generate_magnitude_dataset(size=1000, seed=44):
    """Gera valores de diferentes ordens de magnitude."""
    rng = random.Random(seed)
    values = []

    for _ in range(size):
        exponent = rng.randint(-10, 10)
        mantissa = rng.uniform(-1.0, 1.0)
        values.append(mantissa * (10 ** exponent))

    return values


def save_results(results, dataset_name, output_file):
    """Salva as métricas em formato CSV."""

    fields = [
        "dataset",
        "format",
        "input_samples",
        "samples",
        "excluded_samples",
        "relative_samples",
        "mae",
        "rmse",
        "max_error",
        "mean_relative_error",
        "median_relative_error",
        "p95_relative_error",
        "p99_relative_error",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for format_name, metrics in results.items():
            writer.writerow({
                "dataset": dataset_name,
                "format": format_name,
                "input_samples": metrics["input_samples"],
                "samples": metrics["samples"],
                "excluded_samples": metrics["excluded_samples"],
                "relative_samples": metrics["relative_samples"],
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "max_error": metrics["max_error"],
                "mean_relative_error": metrics["mean_relative_error"],
                "median_relative_error": metrics["median_relative_error"],
                "p95_relative_error": metrics["p95_relative_error"],
                "p99_relative_error": metrics["p99_relative_error"],
            })


def main():
    output_dir = PROJECT_ROOT / "results"
    output_dir.mkdir(exist_ok=True)

    datasets = {
        "near_zero": generate_near_zero_dataset(),
        "moderate_values": generate_moderate_dataset(),
        "random_magnitudes": generate_magnitude_dataset(),
    }

    for dataset_name, values in datasets.items():

        print(f"\n{'=' * 50}")
        print(f"Experimento: {dataset_name}")
        print(f"Quantidade de valores: {len(values)}")

        results = compare_numeric_formats(values)

        output_file = output_dir / f"{dataset_name}.csv"

        save_results(results, dataset_name, output_file)

        print("\nResultados:")

        for format_name, metrics in results.items():
            print(f"\n{format_name}")
            print(f"  MAE:              {metrics['mae']:.10g}")
            print(f"  RMSE:             {metrics['rmse']:.10g}")
            print(f"  Erro relativo P95: {metrics['p95_relative_error']:.10g}")
            print(f"  Amostras válidas: {metrics['samples']}")
            print(f"  Amostras excluídas: {metrics['excluded_samples']}")

        print(f"\nCSV salvo em: {output_file}")


if __name__ == "__main__":
    main()